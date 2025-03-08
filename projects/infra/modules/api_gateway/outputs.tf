# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# API Gateway outputs

output "api_gateway_id" {
  description = "The ID of the API Gateway endpoint"
  value       = aws_api_gateway_rest_api.api.id
}

output "api_gateway_invoke_url" {
  description = "The URL of the API Gateway endpoint"
  value       = aws_api_gateway_deployment.api_deployment.invoke_url
}

output "api_gateway_execution_arn" {
  description = "ARN for API Gateway execution"
  value       = aws_api_gateway_rest_api.api.execution_arn
}
