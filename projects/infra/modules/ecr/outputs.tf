# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECR outputs

output "ecr_processor_repository_url" {
  description = "URL of ECR repository for processor image"
  value       = aws_ecr_repository.processor.repository_url
}

output "ecr_processor_repository_name" {
  description = "Name of ECR repository for processor image"
  value       = aws_ecr_repository.processor.name
}
