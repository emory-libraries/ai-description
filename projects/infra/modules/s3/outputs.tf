# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# modules/s3/outputs.tf

output "uploads_bucket_name" {
  description = "The name of the S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.id
}

output "uploads_bucket_arn" {
  description = "The ARN of the S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.arn
}

output "uploads_bucket_id" {
  description = "The ID of the S3 bucket for uploads"
  value       = aws_s3_bucket.uploads.id
}

output "website_bucket_id" {
  description = "ID of the website bucket"
  value       = aws_s3_bucket.website.id
}

output "website_bucket_name" {
  description = "Name of the website bucket"
  value       = aws_s3_bucket.website.bucket
}

output "website_bucket_arn" {
  description = "ARN of the website bucket"
  value       = aws_s3_bucket.website.arn
}

output "website_bucket_regional_domain_name" {
  description = "Regional domain name of the website bucket"
  value       = aws_s3_bucket.website.bucket_regional_domain_name
}

output "s3_website_endpoint" {
  description = "URL of S3 frontend"
  value       = aws_s3_bucket_website_configuration.website.website_endpoint
}
