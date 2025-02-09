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

# CloudWatch module
module "cloudwatch" {
  source = "./modules/cloudwatch"

  deployment_name = var.deployment_name
}

# VPC module
module "vpc" {
  source = "./modules/vpc"

  deployment_name = var.deployment_name
  vpc_id          = var.vpc_id
}

# DynamoDB module for job metadata storage
module "dynamodb" {
  source = "./modules/dynamodb"

  deployment_name = var.deployment_name
}

# SQS module for "works" queue
module "sqs" {
  source     = "./modules/sqs"
  queue_name = "works-queue-${var.deployment_name}"

  # Optional args
  delay_seconds              = 5
  max_message_size           = 2048
  message_retention_seconds  = 86400 # 1 day
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 60
}

# S3 module for uploads and results buckets
module "s3" {
  source = "./modules/s3"

  deployment_name = var.deployment_name
}

# Base IAM module for core roles
module "iam" {
  source = "./modules/iam"
  depends_on = [
    module.dynamodb,
    module.sqs,
    module.s3,
    module.vpc,
  ]

  deployment_name     = var.deployment_name
  works_table_arn     = module.dynamodb.works_table_arn
  uploads_bucket_arn  = module.s3.uploads_bucket_arn
  results_bucket_arn  = module.s3.results_bucket_arn
  sqs_works_queue_arn = module.sqs.queue_arn
  vpc_s3_endpoint_id  = module.vpc.vpc_s3_endpoint_id
}

# ECS module for Fargate tasks
module "ecs" {
  source = "./modules/ecs"
  depends_on = [
    module.dynamodb,
    module.cloudwatch,
    module.s3,
    module.sqs,
    module.vpc,
    module.iam,
  ]

  deployment_name            = var.deployment_name
  stage_name                 = var.stage_name
  cluster_name               = "ai-description-${var.deployment_name}"
  works_table_name           = module.dynamodb.works_table_name
  centralized_log_group_name = module.cloudwatch.cloudwatch_log_group_name
  uploads_bucket_name        = module.s3.uploads_bucket_name
  results_bucket_name        = module.s3.results_bucket_name
  sqs_queue_url              = module.sqs.queue_url
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_subnet_ids
  task_execution_role_arn    = module.iam.ecs_task_execution_role_arn
  task_role_arn              = module.iam.ecs_task_role_arn
}

# Lambda functions for API endpoints and starting ECS tasks
module "lambda" {
  source = "./modules/lambda"
  depends_on = [
    module.sqs,
    module.vpc,
    module.dynamodb,
    module.s3,
    module.iam,
    module.ecs
  ]

  deployment_name         = var.deployment_name
  sqs_queue_url           = module.sqs.queue_url
  subnet_ids              = module.vpc.private_subnet_ids
  works_table_name        = module.dynamodb.works_table_name
  uploads_bucket_name     = module.s3.uploads_bucket_name
  results_bucket_name     = module.s3.results_bucket_name
  base_lambda_role_arn    = module.iam.base_lambda_role_arn
  task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_cluster_name        = module.ecs.cluster_name
  ecs_task_definition_arn = module.ecs.task_definition_arn
  security_group_ids      = module.vpc.vpc_security_group_ids
}

# API Gateway configuration
module "api_gateway" {
  source     = "./modules/api_gateway"
  depends_on = [module.lambda, module.iam]

  deployment_name     = var.deployment_name
  stage_name          = var.stage_name
  lambda              = module.lambda.function_arns
  cloudwatch_role_arn = module.iam.api_gateway_cloudwatch_role_arn
}

# Eventbridge module
module "eventbridge" {
  source     = "./modules/eventbridge"
  depends_on = [module.sqs, module.lambda]

  deployment_name         = var.deployment_name
  sqs_works_queue_name    = module.sqs.queue_name
  run_ecs_task_lambda_arn = module.lambda.function_arns["run_ecs_task"]
}
