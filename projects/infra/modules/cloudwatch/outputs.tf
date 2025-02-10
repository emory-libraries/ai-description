# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Cloudwatch outputs

output "cloudwatch_log_group_name" {
  description = "The name of CloudWatch log group"
  value       = aws_cloudwatch_log_group.app_logs.name
}
