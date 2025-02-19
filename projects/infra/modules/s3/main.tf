# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# S3 module

locals {
  force_destroy = var.deployment_stage == "dev" ? true : false
}

# Uploads bucket
resource "aws_s3_bucket" "uploads" {
  bucket        = "${var.deployment_prefix_global}-uploads"
  force_destroy = local.force_destroy
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads_encryption" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "uploads_public_access_block" {
  bucket = aws_s3_bucket.uploads.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Logs bucket
resource "aws_s3_bucket" "logs" {
  bucket        = "${var.deployment_prefix_global}-logs"
  force_destroy = local.force_destroy
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs_encryption" {
  bucket = aws_s3_bucket.logs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "logs_public_access_block" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lambda code bucket
resource "aws_s3_bucket" "lambda_code" {
  bucket        = "${var.deployment_prefix_global}-lambda-code"
  force_destroy = local.force_destroy
}
