# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# VPC variables

variable "vpc_id" {
  description = "ID of an existing VPC (optional - leave empty to create new VPC)"
  type        = string
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "azs" {
  description = "Availability zones"
  type        = list(string)
  default     = ["a", "b"]
}

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "enable_vpc_endpoints" {
  type = bool
}

variable "flow_log_retention_days" {
  description = "Number of days to retain VPC flow logs in CloudWatch"
  type        = number
  default     = 7
}
