# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# modules/s3/main.tf

locals {
  force_destroy = var.deployment_stage == "dev" ? true : false
}

# Uploads bucket
resource "aws_s3_bucket" "uploads" {
  bucket        = "${var.deployment_prefix_global}-uploads"
  force_destroy = local.force_destroy
 
}

resource "aws_s3_bucket_lifecycle_configuration" "ninetydays" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    id = "90days"
    expiration {
       days = 90
     }
    status = "Enabled" 
  }



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

# Frontend bucket
resource "aws_s3_bucket" "website" {
  bucket = "${var.deployment_prefix_global}-website"

  tags = {
    Name = "WebsiteBucket"
  }
}

resource "aws_s3_bucket_ownership_controls" "website" {
  bucket = aws_s3_bucket.website.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket                  = aws_s3_bucket.website.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable static website hosting
resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html" # For SPA (Single Page Applications), redirect errors to index
  }
}
