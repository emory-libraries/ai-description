# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# RDS variables

variable "deployment_name" {
  description = "Unique name for this deployment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where Aurora will be deployed"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for Aurora"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID of ECS tasks"
  type        = string
}

# New variables for Aurora configuration
variable "min_capacity" {
  description = "Minimum Aurora capacity unit (ACU)"
  type        = number
  default     = 0.0
}

variable "max_capacity" {
  description = "Maximum Aurora capacity unit (ACU)"
  type        = number
  default     = 1.0
}

variable "auto_pause_seconds" {
  description = "Seconds before Aurora automatically pauses"
  type        = number
  default     = 3600
}

variable "skip_final_snapshot" {
  description = "Whether to skip final snapshot when destroying database"
  type        = bool
  default     = true
}
