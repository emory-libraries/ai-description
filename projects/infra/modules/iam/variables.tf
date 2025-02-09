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

variable "results_bucket_arn" {
  description = "ARN of the S3 bucket for results"
  type        = string
}

variable "deployment_name" {
  description = "Unique name of deployment"
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
