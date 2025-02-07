# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# DynamoDB outputs

output "works_table_name" {
  description = "The name of the DynamoDB jobs table"
  value       = aws_dynamodb_table.jobs.name
}

output "jobs_table_arn" {
  description = "The ARN of the DynamoDB jobs table"
  value       = aws_dynamodb_table.jobs.arn
}
