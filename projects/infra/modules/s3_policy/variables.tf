# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

variable "bucket_id" {
  description = "ID of frontend bucket"
  type        = string
}

variable "bucket_arn" {
  description = "ARN of frontend bucket"
  type        = string
}

variable "cloudfront_distribution_arn" {
  description = "ARN of Cloudfront distribution"
  type        = string
}
