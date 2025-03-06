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
  description = "Unique name of the deployment"
  type        = string
  nullable    = false

  validation {
    condition = (
      length(var.deployment_name) >= 3 &&
      length(var.deployment_name) <= 12 &&
      can(regex("^[a-z][a-z0-9-]*$", var.deployment_name))
    )
    error_message = "The deployment_name must be between 3 and 12 characters, start with a lowercase letter, and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "deployment_stage" {
  description = "Deployment stage name for the environment"
  type        = string
  default     = "dev"
}

# Add this variable:
variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "ai-description"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*$", var.app_name))
    error_message = "app_name must start with a letter and only contain lowercase letters, numbers, and hyphens"
  }
}


variable "vpc_id" {
  description = "ID of an existing VPC (optional - leave empty to create new VPC)"
  type        = string
  default     = ""
}

variable "enable_vpc_endpoints" {
  type    = bool
  default = true
}
