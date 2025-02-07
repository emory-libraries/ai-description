# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Lambda functions module

data "aws_region" "current" {}

# Create S3 bucket for Lambda code (keep this for other functions)
resource "aws_s3_bucket" "lambda_code" {
  bucket = "lambda-code-${var.deployment_name}"
}

# Create ECR repository for predict Lambda
resource "aws_ecr_repository" "predict_lambda" {
  name         = "predict-lambda-${var.deployment_name}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Build and push Docker image for predict Lambda
resource "null_resource" "predict_lambda_image" {
  triggers = {
    python_file = filemd5("${path.module}/src/functions/predict/index.py")
    dockerfile  = filemd5("${path.module}/src/functions/predict/Dockerfile")
    src_hash    = sha1(join("", [for f in fileset("${path.root}/../src", "**") : filesha1("${path.root}/../src/${f}")]))
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${aws_ecr_repository.predict_lambda.repository_url}
      cd ${path.root}/..
      docker build -t ${aws_ecr_repository.predict_lambda.repository_url}:latest -f infra/modules/lambda/src/functions/predict/Dockerfile .
      docker push ${aws_ecr_repository.predict_lambda.repository_url}:latest
    EOF
  }
}

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
      environment = {
        WORKS_TABLE_NAME = var.works_table_name
        SQS_QUEUE_URL    = var.sqs_queue_url
      }
    }
    jobs = {
      source_dir  = "${path.module}/src/functions/jobs"
      description = "Manages job status tracking and updates"
      timeout     = 15
      environment = {
        WORKS_TABLE_NAME = var.works_table_name
      }
    }
    results = {
      source_dir  = "${path.module}/src/functions/results"
      description = "Handles retrieval and delivery of processing results"
      timeout     = 30
      environment = {
        RESULTS_BUCKET_NAME = var.results_bucket_name
        WORKS_TABLE_NAME    = var.works_table_name
      }
    }
    ecs = {
      source_dir  = "${path.module}/src/functions/ecs"
      description = "Manages ECS task operations for processing jobs"
      timeout     = 30
      environment = {
        ECS_CLUSTER_NAME        = var.ecs_cluster_name
        ECS_TASK_DEFINITION_ARN = var.ecs_task_definition_arn
        ECS_SUBNET_IDS          = join(",", var.subnet_ids)
        ECS_SECURITY_GROUP_IDS  = join(",", var.security_group_ids)
        TASK_EXECUTION_ROLE_ARN = var.task_execution_role_arn
      }
    }
    predict = {
      source_dir  = "${path.module}/src/functions/predict"
      description = "Real-time endpoint for item to skill matching"
      timeout     = 30
      memory_size = 2048
      environment = {}
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
    null_resource.predict_lambda_image,
    data.archive_file.function_zips
  ]

  for_each      = local.lambda
  function_name = "${each.key}-${var.deployment_name}"
  description   = each.value.description
  role          = var.base_lambda_role_arn
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
    for_each = each.key == "predict" ? [1] : []
    content {
      command = ["index.handler"]
    }
  }

  package_type     = each.key == "predict" ? "Image" : "Zip"
  image_uri        = each.key == "predict" ? "${aws_ecr_repository.predict_lambda.repository_url}:latest" : null
  filename         = each.key == "predict" ? null : data.archive_file.function_zips[each.key].output_path
  handler          = each.key == "predict" ? null : "index.handler"
  runtime          = each.key == "predict" ? null : "python3.12"
  source_code_hash = each.key == "predict" ? null : filebase64sha256("${each.value.source_dir}/index.py")
}
