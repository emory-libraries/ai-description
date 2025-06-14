# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Lambda functions module

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Create dist directories for other functions
resource "null_resource" "create_dist_dirs" {
  for_each = toset([
    "${path.module}/dist/functions"
  ])

  triggers = {
    dir_path = each.value
  }

  provisioner "local-exec" {
    command = "mkdir -p ${each.value}"
  }

}

# Lambda function configurations
locals {
  lambda = {
    create_job = {
      source_dir  = "${path.module}/src/functions/create_job"
      description = "Create new batch job"
      timeout     = 30
      role_arn    = var.create_job_role_arn
      environment = {
        WORKS_TABLE_NAME        = var.works_table_name
        SQS_QUEUE_URL           = var.sqs_queue_url
        ECS_CLUSTER_NAME        = var.ecs_cluster_name
        ECS_CONTAINER_NAME      = "${var.deployment_prefix}-processing-container"
        ECS_TASK_DEFINITION_ARN = var.ecs_task_definition_arn
        ECS_SUBNET_IDS          = join(",", var.private_subnet_ids)
        ECS_SECURITY_GROUP_IDS  = join(",", [var.ecs_security_group_id])
        TASK_EXECUTION_ROLE_ARN = var.task_execution_role_arn
      }
    }
    job_progress = {
      source_dir  = "${path.module}/src/functions/job_progress"
      description = "Manages job status tracking and updates"
      timeout     = 15
      role_arn    = var.job_progress_role_arn
      environment = {
        WORKS_TABLE_NAME = var.works_table_name
      }
    }
    overall_progress = {
      source_dir  = "${path.module}/src/functions/overall_progress"
      description = "Checks SQS and ECS status"
      timeout     = 15
      role_arn    = var.overall_progress_role_arn
      environment = {
        SQS_QUEUE_URL           = var.sqs_queue_url
        ECS_CLUSTER_NAME        = var.ecs_cluster_name
        ECS_TASK_DEFINITION_ARN = var.ecs_task_definition_arn
      }
    }
    get_results = {
      source_dir  = "${path.module}/src/functions/get_results"
      description = "Retrieve results for a work in a job"
      timeout     = 30
      role_arn    = var.get_results_role_arn
      environment = {
        WORKS_TABLE_NAME = var.works_table_name
      }
    }
    get_presigned_url = {
      source_dir  = "${path.module}/src/functions/get_presigned_url"
      description = "Get a pre-signed URL for an S3 item"
      timeout     = 30
      role_arn    = var.get_presigned_url_role_arn
      environment = {}
    }
    update_results = {
      source_dir  = "${path.module}/src/functions/update_results"
      description = "Updates results for a work in a job"
      timeout     = 30
      role_arn    = var.update_results_role_arn
      environment = {
        WORKS_TABLE_NAME = var.works_table_name
      }
    }
  }
}

# Create ZIP archives for each function (except predict)
data "archive_file" "function_zips" {
  depends_on = [null_resource.create_dist_dirs]

  for_each    = local.lambda
  type        = "zip"
  source_dir  = each.value.source_dir
  output_path = "${path.module}/dist/functions/${each.key}.zip"
}

# Create Lambda functions
resource "aws_lambda_function" "functions" {
  depends_on = [
    data.archive_file.function_zips
  ]

  for_each      = local.lambda
  function_name = "${var.deployment_prefix}-${each.key}"
  description   = each.value.description
  role          = each.value.role_arn
  timeout       = each.value.timeout
  memory_size   = lookup(each.value, "memory_size", 256)

  dynamic "environment" {
    for_each = each.value.environment != null ? [each.value.environment] : []
    content {
      variables = environment.value
    }
  }

  # Use container image for predict Lambda, ZIP for others
  dynamic "image_config" {
    for_each = []
    content {
      command = ["index.handler"]
    }
  }

  package_type     = "Zip"
  image_uri        = null
  filename         = data.archive_file.function_zips[each.key].output_path
  handler          = "index.handler"
  runtime          = "ruby3.3"
  source_code_hash = filebase64sha256("${each.value.source_dir}/index.rb")
}
