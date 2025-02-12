# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Lambda functions outputs

output "function_arns" {
  description = "Map of Lambda function ARNs"
  value = {
    for k, v in aws_lambda_function.functions : k => v.arn
  }
}

output "function_names" {
  description = "Map of Lambda function names"
  value = {
    for k, v in aws_lambda_function.functions : k => v.function_name
  }
}
