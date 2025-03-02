# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# CloudFront variables

variable "deployment_prefix" {
  description = "Prefix for resource naming"
  type        = string
}

variable "website_bucket_regional_domain_name" {
  description = "Regional domain name of the website S3 bucket"
  type        = string
}

variable "api_gateway_deployment_stage" {
  description = "Deployment stage of API Gateway"
  type        = string
}

variable "api_gateway_invoke_url" {
  description = "Invoke URL of API Gateway"
  type        = string
}
