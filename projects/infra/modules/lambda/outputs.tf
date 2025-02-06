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

output "start_ecs_task_lambda_arn" {
  value = aws_lambda_function.functions["ecs"].arn
}

output "lambda" {
  description = "The names of the Lambda functions"
  value = {
    uploads = aws_lambda_function.functions["uploads"].arn
    jobs    = aws_lambda_function.functions["jobs"].arn
    results = aws_lambda_function.functions["results"].arn
    predict = aws_lambda_function.functions["predict"].arn
  }
}

output "predict_ecr_repository_url" {
  description = "URL of the ECR repository for predict Lambda"
  value       = aws_ecr_repository.predict_lambda.repository_url
}
