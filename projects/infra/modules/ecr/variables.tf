# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECR variables

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "deployment_stage" {
  description = "Deployment stage name for the environment"
  type        = string
}
