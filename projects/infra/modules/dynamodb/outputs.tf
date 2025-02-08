# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# DynamoDB outputs

output "works_table_name" {
  description = "The name of the DynamoDB works table"
  value       = aws_dynamodb_table.works.name
}

output "works_table_arn" {
  description = "The ARN of the DynamoDB works table"
  value       = aws_dynamodb_table.works.arn
}
