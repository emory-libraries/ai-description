# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# API Gateway variables

variable "lambda" {
  description = "Map of Lambda function ARNs"
  type        = map(string)
}

variable "stage_name" {
  description = "Deployment stage name for environment"
  type        = string
  default     = "dev"
}

variable "deployment_name" {
  description = "Unique name of deployment"
  type        = string
}

variable "cloudwatch_role_arn" {
  description = "ARN of Cloudwatch role"
  type        = string
}
