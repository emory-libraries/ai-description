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
      Environment = var.deployment_stage
      Project     = "ai-description"
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  account_id               = data.aws_caller_identity.current.account_id
  deployment_prefix        = lower("${var.app_name}-${var.deployment_stage}-${var.deployment_name}")
  deployment_prefix_logs   = lower("${var.app_name}/${var.deployment_stage}/${var.deployment_name}")
  deployment_prefix_global = lower("${local.deployment_prefix}-${local.account_id}")
}

# CloudWatch module
module "cloudwatch" {
  source = "./modules/cloudwatch"

  deployment_prefix_logs = local.deployment_prefix_logs
}

# VPC module
module "vpc" {
  source = "./modules/vpc"

  deployment_prefix    = local.deployment_prefix
  vpc_id               = var.vpc_id
  enable_vpc_endpoints = var.enable_vpc_endpoints
}

# ECR module
module "ecr" {
  source = "./modules/ecr"

  deployment_prefix = local.deployment_prefix
  deployment_stage  = var.deployment_stage
}

# DynamoDB module
module "dynamodb" {
  source = "./modules/dynamodb"

  deployment_prefix = local.deployment_prefix
}

# SQS module
module "sqs" {
  source = "./modules/sqs"

  deployment_prefix = local.deployment_prefix

  # Optional args
  delay_seconds              = 5
  max_message_size           = 2048
  message_retention_seconds  = 86400 # 1 day
  receive_wait_time_seconds  = 10
  visibility_timeout_seconds = 60
}

# S3 module
module "s3" {
  source = "./modules/s3"

  deployment_prefix        = local.deployment_prefix
  deployment_prefix_global = local.deployment_prefix_global
  deployment_stage         = var.deployment_stage
}

# IAM module
module "iam" {
  source = "./modules/iam"
  depends_on = [
    module.dynamodb,
    module.sqs,
    module.s3,
    module.vpc,
    module.ecr,
  ]

  deployment_prefix             = local.deployment_prefix
  works_table_arn               = module.dynamodb.works_table_arn
  uploads_bucket_arn            = module.s3.uploads_bucket_arn
  sqs_works_queue_arn           = module.sqs.queue_arn
  vpc_s3_endpoint_id            = module.vpc.vpc_endpoint_ids.s3
  vpc_ecr_api_endpoint_id       = module.vpc.vpc_endpoint_ids.ecr_api
  vpc_ecr_dkr_endpoint_id       = module.vpc.vpc_endpoint_ids.ecr_dkr
  ecr_processor_repository_name = module.ecr.ecr_processor_repository_name
  enable_vpc_endpoints          = var.enable_vpc_endpoints
}

# ECS module
module "ecs" {
  source = "./modules/ecs"
  depends_on = [
    module.ecr,
    module.dynamodb,
    module.cloudwatch,
    module.s3,
    module.sqs,
    module.vpc,
    module.iam,
  ]

  deployment_prefix            = local.deployment_prefix
  deployment_prefix_logs       = local.deployment_prefix_logs
  deployment_stage             = var.deployment_stage
  ecr_processor_repository_url = module.ecr.ecr_processor_repository_url
  works_table_name             = module.dynamodb.works_table_name
  centralized_log_group_name   = module.cloudwatch.cloudwatch_log_group_name
  uploads_bucket_name          = module.s3.uploads_bucket_name
  sqs_queue_url                = module.sqs.queue_url
  vpc_id                       = module.vpc.vpc_id
  task_execution_role_arn      = module.iam.ecs_task_execution_role_arn
  task_role_arn                = module.iam.ecs_task_role_arn
}

# Lambda module
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

  deployment_prefix       = local.deployment_prefix
  sqs_queue_url           = module.sqs.queue_url
  private_subnet_ids      = module.vpc.private_subnet_ids
  works_table_name        = module.dynamodb.works_table_name
  uploads_bucket_name     = module.s3.uploads_bucket_name
  base_lambda_role_arn    = module.iam.base_lambda_role_arn
  task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_cluster_name        = module.ecs.cluster_name
  ecs_task_definition_arn = module.ecs.task_definition_arn
  ecs_security_group_id   = module.vpc.ecs_security_group_id
  vpc_security_group_id   = module.vpc.vpc_endpoints_security_group_id
}

# API Gateway module
module "api_gateway" {
  source     = "./modules/api_gateway"
  depends_on = [module.lambda, module.iam]

  deployment_prefix   = local.deployment_prefix
  deployment_stage    = var.deployment_stage
  lambda              = module.lambda.function_arns
  cloudwatch_role_arn = module.iam.api_gateway_cloudwatch_role_arn
}
