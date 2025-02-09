# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# S3 outputs

output "uploads_bucket_name" {
  description = "The name of the S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.id
}

output "uploads_bucket_arn" {
  description = "The ARN of the S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.arn
}

output "results_bucket_arn" {
  description = "The ARN of the S3 bucket for results"
  value       = aws_s3_bucket.results.arn
}
