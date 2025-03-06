# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# S3 variables

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "deployment_prefix_global" {
  description = "Global unique name of the deployment"
  type        = string
}

variable "deployment_stage" {
  description = "Deployment stage name for the environment"
  type        = string
}

variable "application_uri" {
  description = "URI of the application"
  type        = string
}

variable "cognito_domain_url" {
  description = "Cognito domain URL"
  type        = string
}

variable "cognito_client_id" {
  description = "Cognito client ID"
  type        = string
}
