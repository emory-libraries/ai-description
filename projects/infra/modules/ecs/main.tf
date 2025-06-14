# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECS module

data "aws_region" "current" {}

locals {
  project_root_path = "${path.root}/../.."
  ecs_src_path      = "${path.module}/src"
  lib_path          = "${local.project_root_path}/lib/ruby"
  ecs_src_files     = fileset(local.ecs_src_path, "**")
  package_src_files = fileset(local.lib_path, "**")
  ecs_src_hash      = sha256(join("", [for f in local.ecs_src_files : filesha256("${local.ecs_src_path}/${f}")]))
  package_src_hash  = sha256(join("", [for f in local.package_src_files : filesha256("${local.lib_path}/${f}")]))
  combined_src_hash = sha256("${local.ecs_src_hash}${local.package_src_hash}")
  image_tag         = substr(local.combined_src_hash, 0, 8) # Using first 8 characters of the hash for brevity
}

# Push latest image
resource "null_resource" "push_image" {
  triggers = {
    ecr_repository_url = var.ecr_processor_repository_url
    combined_src_hash  = local.combined_src_hash
  }

  provisioner "local-exec" {
    interpreter = ["bash", "-c"] # Explicitly specify bash interpreter
    command     = <<EOF
      echo "Starting Docker build and push process"
      aws ecr get-login-password --region ${data.aws_region.current.name} | docker login --username AWS --password-stdin ${var.ecr_processor_repository_url}
      docker build -t ${var.ecr_processor_repository_url}:${local.image_tag} -f ${local.ecs_src_path}/Dockerfile.ruby ${local.project_root_path} || exit 1
      docker push ${var.ecr_processor_repository_url}:${local.image_tag} || exit 1
      echo "Docker build and push process completed"
    EOF
    on_failure  = fail
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "cluster" {
  name = "${var.deployment_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Task Definition using Fargate with increased ephemeral storage
resource "aws_ecs_task_definition" "task" {
  family                   = "${var.deployment_prefix}-processing-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024" # 1 vCPU
  memory                   = "2048" # 2 GB RAM
  execution_role_arn       = var.task_execution_role_arn
  task_role_arn            = var.task_role_arn

  # Configure ephemeral storage up to 100 GB
  ephemeral_storage {
    size_in_gib = 100
  }

  # Container definitions
  container_definitions = jsonencode([
    {
      name      = "${var.deployment_prefix}-processing-container"
      image     = "${var.ecr_processor_repository_url}:${local.image_tag}"
      cpu       = 1024
      memory    = 2048
      essential = true
      environment = [
        { name = "AWS_REGION", value = data.aws_region.current.name },
        { name = "UPLOADS_BUCKET_NAME", value = var.uploads_bucket_name },
        { name = "WORKS_TABLE_NAME", value = var.works_table_name },
        { name = "SQS_QUEUE_URL", value = var.sqs_queue_url },
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = var.centralized_log_group_name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "${var.deployment_prefix_logs}/processing-logs"
        }
      }
    }
  ])
}
