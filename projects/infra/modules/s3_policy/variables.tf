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
