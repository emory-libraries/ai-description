# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Main module

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">=5.73.0"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = var.stage_name
      Project     = "ai-description"
      ManagedBy   = "terraform"
    }
  }
}

# VPC module
module "vpc" {
  source = "./modules/vpc"

  deployment_name = var.deployment_name
  vpc_id          = var.vpc_id
}

# RDS module
module "rds" {
  source = "./modules/rds"

  deployment_name       = var.deployment_name
  vpc_id                = module.vpc.vpc_id
  subnet_ids            = module.vpc.private_subnet_ids
  ecs_security_group_id = module.ecs.security_group_ids[0]

  # Optional: customize scaling configuration
  min_capacity       = 0.5  # Minimum of 0.5 ACU
  max_capacity       = 2.0  # Maximum of 2 ACU
  auto_pause_seconds = 1800 # Auto-pause after 30 minutes of inactivity
}

# DynamoDB module for job metadata storage
module "dynamodb" {
  source = "./modules/dynamodb"

  deployment_name = var.deployment_name
}

# Base IAM module for core roles
module "iam" {
  source = "./modules/iam"

  deployment_name           = var.deployment_name
  jobs_table_arn            = module.dynamodb.jobs_table_arn
  uploads_bucket_arn        = module.s3.uploads_bucket_arn
  results_bucket_arn        = module.s3.results_bucket_arn
  db_credentials_secret_arn = module.rds.credentials_secret_arn
}

# ECS module for Fargate tasks
module "ecs" {
  source = "./modules/ecs"

  deployment_name           = var.deployment_name
  cluster_name              = "ai-description-${var.deployment_name}"
  uploads_bucket_name       = module.s3.uploads_bucket_name
  results_bucket_name       = module.s3.results_bucket_name
  jobs_table_name           = module.dynamodb.jobs_table_name
  vpc_id                    = module.vpc.vpc_id
  subnet_ids                = module.vpc.private_subnet_ids
  task_execution_role_arn   = module.iam.ecs_task_execution_role_arn
  task_role_arn             = module.iam.ecs_task_role_arn
  stage_name                = var.stage_name
  db_credentials_secret_arn = module.rds.credentials_secret_arn
  db_host                   = module.rds.cluster_endpoint
}

# Lambda functions for API endpoints and starting ECS tasks
module "lambda" {
  source = "./modules/lambda"

  deployment_name         = var.deployment_name
  uploads_bucket_name     = module.s3.uploads_bucket_name
  results_bucket_name     = module.s3.results_bucket_name
  jobs_table_name         = module.dynamodb.jobs_table_name
  base_lambda_role_arn    = module.iam.base_lambda_role_arn
  ecs_cluster_name        = module.ecs.cluster_name
  ecs_task_definition_arn = module.ecs.task_definition_arn
  subnet_ids              = module.vpc.private_subnet_ids
  security_group_ids      = module.ecs.security_group_ids
  task_execution_role_arn = module.iam.ecs_task_execution_role_arn
}

# S3 module for uploads and results buckets
module "s3" {
  source = "./modules/s3"

  deployment_name           = var.deployment_name
  start_ecs_task_lambda_arn = module.lambda.start_ecs_task_lambda_arn
}

# API Gateway configuration
module "api_gateway" {
  source = "./modules/api_gateway"

  deployment_name = var.deployment_name
  lambda          = module.lambda.lambda
  stage_name      = var.stage_name
}

# VPC Endpoint for S3
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = module.vpc.vpc_id
  service_name      = "com.amazonaws.${var.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids = concat(
    module.vpc.public_route_table_ids,
    module.vpc.private_route_table_ids
  )
}

# VPC Endpoint policy
resource "aws_vpc_endpoint_policy" "s3_policy" {
  vpc_endpoint_id = aws_vpc_endpoint.s3.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowS3Access"
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          module.s3.uploads_bucket_arn,
          "${module.s3.uploads_bucket_arn}/*",
          module.s3.results_bucket_arn,
          "${module.s3.results_bucket_arn}/*"
        ]
      }
    ]
  })
}

# VPC Endpoint for Secrets Manager
resource "aws_vpc_endpoint" "secretsmanager" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.secretsmanager"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnet_ids
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true
}

resource "aws_security_group" "vpc_endpoints" {
  name        = "vpc-endpoints-${var.deployment_name}"
  description = "Security group for VPC endpoints"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = module.ecs.security_group_ids
  }
}

# CloudWatch Log Group for centralized logging
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/ai-description-poc/logs-${var.deployment_name}"
  retention_in_days = 30
}
