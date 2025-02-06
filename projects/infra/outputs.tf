# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Main outputs

output "api_endpoint" {
  description = "The URL of the API Gateway endpoint"
  value       = module.api_gateway.api_endpoint
}

output "uploads_bucket_name" {
  description = "The name of the S3 bucket for uploads"
  value       = module.s3.uploads_bucket_name
}

output "results_bucket_name" {
  description = "The name of the S3 bucket for results"
  value       = module.s3.results_bucket_name
}

output "jobs_table_name" {
  description = "The name of the DynamoDB table"
  value       = module.dynamodb.jobs_table_name
}

output "ecs_cluster_name" {
  description = "The name of the ECS cluster"
  value       = module.ecs.cluster_name
}

output "lambda_function_names" {
  description = "The names of the Lambda functions"
  value = {
    uploads = module.lambda.lambda["uploads"]
    jobs    = module.lambda.lambda["jobs"]
    results = module.lambda.lambda["results"]
    ecs     = module.lambda.start_ecs_task_lambda_arn
  }
}

output "results_bucket_arn" {
  description = "The ARN of the S3 bucket for results"
  value       = module.s3.results_bucket_arn
}

output "database_endpoint" {
  description = "Aurora database endpoint"
  value       = module.rds.cluster_endpoint
}

output "database_credentials_secret_arn" {
  description = "ARN of database credentials in Secrets Manager"
  value       = module.rds.credentials_secret_arn
}
