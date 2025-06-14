# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# modules/api_gateway/variables.tf

variable "deployment_stage" {
  description = "Deployment stage name for the environment"
  type        = string
  default     = "dev"
}

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "lambda_function_arns" {
  description = "Map of Lambda function ARNs"
  type        = map(string)
}

variable "lambda_invoke_arns" {
  description = "Map of Lambda invocation function ARNs"
  type        = map(string)
}

variable "lambda_names" {
  description = "Map of Lambda names"
  type        = map(string)
}

variable "api_gateway_role_arn" {
  description = "API Gateway's role ARN"
  type        = string
}

variable "website_bucket_name" {
  description = "Name of the S3 bucket containing the static website files"
  type        = string
}
