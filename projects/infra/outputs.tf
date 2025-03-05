# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Main outputs

output "api_gateway_invoke_url" {
  description = "The URL of the API Gateway endpoint"
  value       = module.api_gateway.api_gateway_invoke_url
}

output "uploads_bucket_name" {
  description = "The name of the S3 bucket for uploads"
  value       = module.s3.uploads_bucket_name
}

output "works_table_name" {
  description = "The name of the DynamoDB table"
  value       = module.dynamodb.works_table_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "lambda_function_names" {
  description = "The names of the Lambda functions"
  value       = module.lambda.function_names
}

output "cloudfront_url" {
  description = "URL of Cloudfront"
  value       = module.cloudfront.distribution_domain_name
}

output "target_function_name" {
  value = module.lambda.function_arns["authorize"]
}

output "authorizer_uri" {
  value = module.lambda.invoke_arns["authorize"]
}
