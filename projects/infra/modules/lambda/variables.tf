# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Lambda functions variables

variable "uploads_bucket_name" {
  description = "Name of the S3 bucket for uploads"
  type        = string
}

variable "works_table_name" {
  description = "Name of the DynamoDB jobs table"
  type        = string
}

variable "accounts_table_name" {
  description = "Name of the DynamoDB accounts table"
  type        = string
}

variable "sqs_queue_url" {
  description = "URL of SQS queue"
  type        = string
}

variable "base_lambda_role_arn" {
  description = "ARN of the base Lambda role"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "ecs_task_definition_arn" {
  description = "ARN of the ECS task definition"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of subnet IDs for ECS tasks"
  type        = list(string)
}

variable "vpc_security_group_id" {
  description = "Aecurity group ID for VPC"
  type        = string
}

variable "ecs_security_group_id" {
  description = "Security group IDs for ECS task"
  type        = string
}

variable "task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}
