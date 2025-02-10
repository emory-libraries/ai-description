# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Main variables

variable "aws_region" {
  description = "AWS region to deploy resources"
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-\\d{1}$", var.aws_region))
    error_message = "Must be a valid AWS region identifier."
  }
}

variable "deployment_name" {
  description = "Unique name of deployment"

  validation {
    condition = (
      length(var.deployment_name) >= 3 &&
      length(var.deployment_name) <= 8 &&
      can(regex("^[a-z][a-z0-9-]*$", var.deployment_name))
    )
    error_message = "The deployment_name must be between 3 and 8 characters, start with a lowercase letter, and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "stage_name" {
  description = "Deployment stage name for environment"
  type        = string
  default     = "dev"
}

variable "vpc_id" {
  description = "ID of an existing VPC (optional - leave empty to create new VPC)"
  type        = string
  default     = ""
}
