# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECS variables

variable "task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  type        = string
}

variable "task_role_arn" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "uploads_bucket_name" {
  description = "Name of the S3 bucket for uploads"
  type        = string
}

variable "works_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "deployment_prefix_logs" {
  description = "Unique name of the deployment for logs"
  type        = string
}

variable "deployment_stage" {
  description = "Deployment stage name for the environment"
  type        = string
}

variable "centralized_log_group_name" {
  description = "Name of the centralized CloudWatch Log Group"
  type        = string
}

variable "sqs_queue_url" {
  description = "URL of SQS queue"
  type        = string
}

variable "ecr_processor_repository_url" {
  description = "URL of ECR repository for processor image"
  type        = string
}
