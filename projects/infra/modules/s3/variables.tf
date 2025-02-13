# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# S3 variables

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "global_deployment_prefix" {
  description = "Global unique name of the deployment"
  type        = string
}

variable "stage_name" {
  description = "Deployment stage name for the environment"
  type        = string
}