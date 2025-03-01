# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# S3 module

locals {
  force_destroy = var.deployment_stage == "dev" ? true : false
  mime_types = {
    ".html" = "text/html"
    ".css"  = "text/css"
    ".js"   = "application/javascript"
    ".json" = "application/json"
    ".png"  = "image/png"
    ".jpg"  = "image/jpeg"
    ".svg"  = "image/svg+xml"
    ".ico"  = "image/x-icon"
  }

  # Use absolute paths based on the current working directory
  working_dir   = abspath(path.root)
  project_root  = dirname(dirname(local.working_dir)) # Go up two levels from projects/infra
  frontend_path = "${local.project_root}/projects/frontend"

  env_js_content = <<-EOT
    window.env = {
      API_URI: "${var.application_uri}",
      COGNITO: {
        authority: "${var.cognito_domain_url}",
        client_id: "${var.cognito_client_id}",
        redirect_uri: "${var.application_uri}",
        post_logout_redirect_uri: "${var.application_uri}",
        scope: "openid",
        response_type: "code",
        loadUserInfo: true,
        metadata: {
          authorization_endpoint: "${var.cognito_domain_url}/oauth2/authorize",
          token_endpoint: "${var.cognito_domain_url}/oauth2/token",
          userinfo_endpoint: "${var.cognito_domain_url}/oauth2/userInfo",
          end_session_endpoint: "${var.cognito_domain_url}/logout"
        }
      }
    };
  EOT
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

# Website deployment - runtime configuration
resource "aws_s3_object" "env_config" {
  bucket       = aws_s3_bucket.website.id
  key          = "env.js"
  content_type = "application/javascript"
  content      = local.env_js_content
  etag         = md5(local.env_js_content)
}

# Build the frontend application
resource "null_resource" "frontend_build" {
  # Only rebuild when frontend files change
  triggers = {
    package_json = fileexists("${local.frontend_path}/package.json") ? filemd5("${local.frontend_path}/package.json") : "not-found"

    src_dir = length(fileset("${local.frontend_path}", "src/**/*.{js,jsx,ts,tsx}")) > 0 ? (
      join("", [for f in fileset("${local.frontend_path}", "src/**/*.{js,jsx,ts,tsx}") :
        filemd5("${local.frontend_path}/${f}")
      ])
    ) : "not-found"
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Building React application..."
      cd "${local.frontend_path}" && \
      mkdir -p ./build && \
      docker run --rm \
        -v "$(pwd):/app" \
        -v "$(pwd)/build:/app/build" \
        -w /app \
        -e NODE_ENV=production \
        -e npm_config_cache=/.npm \
        node:18 \
        bash -c "mkdir -p /.npm && \
          chmod -R 777 /.npm && \
          npm ci --include=dev && \
          npm run build && \
          chmod -R 755 /app/build"

      echo "React build completed successfully"
    EOT
  }
}

# Upload frontend assets to S3
resource "aws_s3_object" "frontend_assets" {
  depends_on = [null_resource.frontend_build]
  for_each   = fileset("${local.frontend_path}/build", "**")

  bucket       = aws_s3_bucket.website.id
  key          = each.value
  source       = "${local.frontend_path}/build/${each.value}"
  etag         = filemd5("${local.frontend_path}/build/${each.value}")
  content_type = lookup(local.mime_types, regex("\\.[^.]+$", each.value), null)
}
