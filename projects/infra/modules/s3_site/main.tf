# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# modules/s3_site/main.tf

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
      API_URL: "${var.api_url}${var.deployment_stage}",
      STAGE_NAME: "${var.deployment_stage}"
    };
  EOT
}

resource "aws_s3_bucket_policy" "website" {
  bucket = var.website_bucket_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAPIGatewayAccess"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${var.website_bucket_arn}/*"
        Condition = {
          StringEquals = {
            "aws:SourceArn" : "${var.api_gateway_execution_arn}/*"
          }
        }
      }
    ]
  })
}

resource "aws_s3_bucket_cors_configuration" "uploads_cors" {
  bucket = var.uploads_bucket_id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["http://localhost:3000", var.frontend_url]
    expose_headers  = ["ETag", "Content-Length", "Content-Type"]
    max_age_seconds = 3000
  }
}

# Website deployment - runtime configuration
resource "aws_s3_object" "env_config" {
  bucket       = var.website_bucket_id
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
      set -e
      echo "Building React application..."
      cd "${local.frontend_path}" && \
      mkdir -p ./build && \
      docker run --rm \
        -v "$(pwd):/app" \
        -v "$(pwd)/build:/app/build" \
        -w /app \
        -e NODE_ENV=production \
        -e PUBLIC_URL="/${var.deployment_stage}" \
        -e DISABLE_ESLINT_PLUGIN=true \
        -e npm_config_cache=/.npm \
        node:18 \
        bash -c "mkdir -p /.npm && \
          chmod -R 777 /.npm && \
          npm ci --include=dev && \
          npm run build && \
          chmod -R 755 /app/build"

      echo "React build completed successfully"
      # Create a build marker with timestamp
      echo "$(date +%s)" > "${local.frontend_path}/build/.build-id"
  }
    EOT
  }
}

# Create a local resource to track build changes
resource "local_file" "build_marker" {
  depends_on = [null_resource.frontend_build]
  filename   = "${path.module}/.build_marker"
  content    = "${timestamp()}-${uuid()}" # This will ensure this changes every time
}

# Upload frontend assets to S3
resource "aws_s3_object" "frontend_assets" {
  depends_on = [null_resource.frontend_build, local_file.build_marker]
  for_each   = fileset("${local.frontend_path}/build", "**/*")

  bucket       = var.website_bucket_id
  key          = each.value
  source       = "${local.frontend_path}/build/${each.value}"
  etag         = fileexists("${local.frontend_path}/build/${each.value}") ? filemd5("${local.frontend_path}/build/${each.value}") : "initial"
  content_type = lookup(local.mime_types, length(regexall("\\.[^.]+$", each.value)) > 0 ? regex("\\.[^.]+$", each.value) : "", null)
}
