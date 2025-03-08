# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# modules/s3_site/variables.tf

variable "deployment_stage" {
  description = "Deployment stage name for the environment"
  type        = string
}

variable "website_bucket_id" {
  description = "ID where website lives"
  type        = string
}

variable "website_bucket_arn" {
  description = "ARN where website lives"
  type        = string
}

variable "uploads_bucket_id" {
  description = "ID of bucket where uploads live"
  type        = string
}

variable "api_gateway_execution_arn" {
  description = "ARN of API Gateway execution"
  type        = string
}

variable "api_url" {
  description = "URL of backend API"
  type        = string
}

variable "frontend_url" {
  description = "URL where frontend will be served"
  type        = string
}
