# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# IAM variables

variable "works_table_arn" {
  description = "ARN of the DynamoDB table"
  type        = string
}

variable "uploads_bucket_arn" {
  description = "ARN of the S3 uploads bucket"
  type        = string
}

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "sqs_works_queue_arn" {
  description = "ARN of the SQS works queue"
  type        = string
}

variable "vpc_s3_endpoint_id" {
  description = "The ID of the VPC's S3 endpoint"
  type        = string
}

variable "vpc_ecr_api_endpoint_id" {
  description = "The ID of the VPC's ECR API endpoint"
  type        = string
}

variable "vpc_ecr_dkr_endpoint_id" {
  description = "The ID of the VPC's ECR DKR endpoint"
  type        = string
}

variable "ecr_processor_repository_name" {
  description = "Name of ECR repository for processor image"
  type        = string
}

variable "enable_vpc_endpoints" {
  description = "Whether or not the application uses VPC endpoints"
  type        = bool
}