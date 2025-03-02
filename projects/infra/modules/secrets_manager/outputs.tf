# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Secrets Manager outputs

output "jwt_secret_arn" {
  description = "ARN of the created secret"
  value       = aws_secretsmanager_secret.jwt_secret.arn
}

output "jwt_secret_name" {
  description = "Name of the created secret"
  value       = aws_secretsmanager_secret.jwt_secret.name
}
