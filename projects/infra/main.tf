# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# main.tf

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
data "aws_region" "current" {}

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

module "secrets_manager" {
  source = "./modules/secrets_manager"

  secret_name             = "${local.deployment_prefix}-jwt-secret2"
  description             = "JWT secret for ai-description application"
  recovery_window_in_days = 0
  generate_random_secret  = true
}

# VPC module
module "vpc" {
  source = "./modules/vpc"

  deployment_prefix    = local.deployment_prefix
  vpc_id               = var.vpc_id
  enable_vpc_endpoints = var.enable_vpc_endpoints
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

# ECR module
module "ecr" {
  source = "./modules/ecr"

  deployment_prefix = local.deployment_prefix
  deployment_stage  = var.deployment_stage
}

# S3 module
module "s3" {
  source = "./modules/s3"

  deployment_prefix        = local.deployment_prefix
  deployment_prefix_global = local.deployment_prefix_global
  deployment_stage         = var.deployment_stage

  # For user interface deployment
  application_uri    = "https://FOO"
  cognito_domain_url = "https://FOO.auth.${var.aws_region}.amazoncognito.com"
  cognito_client_id  = "FOO"
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
    module.secrets_manager,
  ]

  deployment_prefix             = local.deployment_prefix
  works_table_arn               = module.dynamodb.works_table_arn
  accounts_table_arn            = module.dynamodb.accounts_table_arn
  uploads_bucket_arn            = module.s3.uploads_bucket_arn
  sqs_works_queue_arn           = module.sqs.queue_arn
  vpc_s3_endpoint_id            = module.vpc.vpc_endpoint_ids.s3
  vpc_ecr_api_endpoint_id       = module.vpc.vpc_endpoint_ids.ecr_api
  vpc_ecr_dkr_endpoint_id       = module.vpc.vpc_endpoint_ids.ecr_dkr
  ecr_processor_repository_name = module.ecr.ecr_processor_repository_name
  enable_vpc_endpoints          = var.enable_vpc_endpoints
  jwt_secret_arn                = module.secrets_manager.jwt_secret_arn
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
    module.ecs,
    module.secrets_manager
  ]

  deployment_prefix       = local.deployment_prefix
  sqs_queue_url           = module.sqs.queue_url
  private_subnet_ids      = module.vpc.private_subnet_ids
  accounts_table_name     = module.dynamodb.accounts_table_name
  works_table_name        = module.dynamodb.works_table_name
  uploads_bucket_name     = module.s3.uploads_bucket_name
  base_lambda_role_arn    = module.iam.base_lambda_role_arn
  task_execution_role_arn = module.iam.ecs_task_execution_role_arn
  ecs_cluster_name        = module.ecs.cluster_name
  ecs_task_definition_arn = module.ecs.task_definition_arn
  ecs_security_group_id   = module.vpc.ecs_security_group_id
  vpc_security_group_id   = module.vpc.vpc_endpoints_security_group_id
  jwt_secret_name         = module.secrets_manager.jwt_secret_name
  api_gateway_role_name   = module.iam.api_gateway_role_name
}

# API Gateway module
module "api_gateway" {
  source     = "./modules/api_gateway"
  depends_on = [module.lambda, module.iam]

  deployment_prefix       = local.deployment_prefix
  deployment_stage        = var.deployment_stage
  lambda_function_arns    = module.lambda.function_arns
  lambda_invoke_arns      = module.lambda.invoke_arns
  lambda_names            = module.lambda.function_names
  api_gateway_role_arn    = module.iam.api_gateway_role_arn
  authorizer_iam_role_arn = module.iam.base_lambda_role_arn
}

# Cloudfront
module "cloudfront" {
  source = "./modules/cloudfront"
  depends_on = [
    module.s3,
    module.api_gateway,
  ]

  deployment_prefix                   = local.deployment_prefix
  api_gateway_deployment_stage        = var.deployment_stage
  website_bucket_regional_domain_name = module.s3.website_bucket_regional_domain_name
  api_gateway_invoke_url              = module.api_gateway.api_gateway_invoke_url
}

# S3 Policy (to prevent a circular dependency between S3 and Cloudfront)
module "s3_policy" {
  source = "./modules/s3_policy"
  depends_on = [
    module.s3,
    module.cloudfront
  ]
  bucket_id                   = module.s3.website_bucket_id
  bucket_arn                  = module.s3.website_bucket_arn
  cloudfront_distribution_arn = module.cloudfront.distribution_arn
}

# API Gateway policy
resource "aws_api_gateway_rest_api_policy" "cloudfront_access" {
  depends_on  = [module.cloudfront, module.api_gateway]
  rest_api_id = module.api_gateway.api_gateway_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "execute-api:Invoke"
        Resource = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*/*"

        Condition = {
          StringEquals = {
            "aws:SourceArn" = module.cloudfront.distribution_arn
          }
        }
      }
    ]
  })
}
