# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECS module

locals {
  project_root_path = "${path.root}/../.."
  ecs_src_path      = "${path.module}/src"
  package_src_path  = "${local.project_root_path}/lib/image_captioning_assistant"
  ecs_src_files     = fileset(local.ecs_src_path, "**")
  package_src_files = fileset(local.package_src_path, "**")
  ecs_src_hash      = sha256(join("", [for f in local.ecs_src_files : filesha256("${local.ecs_src_path}/${f}")]))
  package_src_hash  = sha256(join("", [for f in local.package_src_files : filesha256("${local.package_src_path}/${f}")]))
  combined_src_hash = sha256("${local.ecs_src_hash}${local.package_src_hash}")
  image_tag         = substr(local.combined_src_hash, 0, 8) # Using first 8 characters of the hash for brevity
}



data "aws_region" "current" {}

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
      aws ecr get-login-password --region ${data.aws_region.current.name} | sudo docker login --username AWS --password-stdin ${var.ecr_processor_repository_url}
      sudo docker build -t ${var.ecr_processor_repository_url}:${local.image_tag} -f ${local.ecs_src_path}/Dockerfile ${local.project_root_path} || exit 1
      sudo docker push ${var.ecr_processor_repository_url}:${local.image_tag} || exit 1
      echo "Docker build and push process completed"
    EOF
    on_failure  = fail
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "cluster" {
  name = var.cluster_name
}

# ECS Task Definition using Fargate with increased ephemeral storage
resource "aws_ecs_task_definition" "task" {
  family                   = "processing-task-${var.deployment_name}"
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
      name      = "processing-container"
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
          awslogs-stream-prefix = "ecs-processing-task"
        }
      }
    }
  ])
}
