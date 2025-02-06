# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECS module

data "aws_region" "current" {}

# ECS Cluster
resource "aws_ecs_cluster" "cluster" {
  name = var.cluster_name
}

# Security Group for ECS Tasks
resource "aws_security_group" "ecs_service_sg" {
  name        = "ecs-service-sg-${var.deployment_name}"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
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
      image     = "${aws_ecr_repository.processor.repository_url}:latest"
      cpu       = 1024
      memory    = 2048
      essential = true
      environment = [
        { name = "AWS_REGION", value = data.aws_region.current.name },
        { name = "UPLOADS_BUCKET_NAME", value = var.uploads_bucket_name },
        { name = "RESULTS_BUCKET_NAME", value = var.results_bucket_name },
        { name = "JOBS_TABLE_NAME", value = var.jobs_table_name },
        { name = "DB_HOST", value = var.db_host },
        { name = "DB_NAME", value = "appdb" },
      ]
      secrets = [
        {
          name      = "DB_CREDENTIALS"
          valueFrom = var.db_credentials_secret_arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = "/ecs/processing-task"
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

# ECR Repository for Docker images
resource "aws_ecr_repository" "processor" {
  name                 = "processor-repo-${var.deployment_name}"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.stage_name == "dev"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Push latest image
resource "null_resource" "push_image" {
  triggers = {
    ecr_repository_url = aws_ecr_repository.processor.repository_url
    dockerfile_hash    = filemd5("${path.module}/src/Dockerfile")
    main_script_hash   = filemd5("${path.module}/src/main.py")
    src_hash           = sha1(join("", [for f in fileset("${path.root}/../src", "**") : filesha1("${path.root}/../src/${f}")]))
  }

  provisioner "local-exec" {
    command = <<EOF
      aws ecr get-login-password --region ${data.aws_region.current.name} | sudo docker login --username AWS --password-stdin ${aws_ecr_repository.processor.repository_url}
      cd ..
      sudo docker build -t ${aws_ecr_repository.processor.repository_url}:latest -f infra/modules/ecs/src/Dockerfile .
      sudo docker push ${aws_ecr_repository.processor.repository_url}:latest
    EOF
  }
}

# CloudWatch Log Group for ECS tasks
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/processing-task-${var.deployment_name}"
  retention_in_days = 30
}
