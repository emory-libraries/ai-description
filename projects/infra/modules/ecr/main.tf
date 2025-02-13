# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECR module

# ECR Repository for Docker images
resource "aws_ecr_repository" "processor" {
  name                 = "${var.deployment_prefix}-processor-repo"
  image_tag_mutability = "MUTABLE"
  force_delete         = var.stage_name == "dev"

  image_scanning_configuration {
    scan_on_push = true
  }
}
