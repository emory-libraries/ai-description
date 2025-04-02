# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# IAM outputs

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.arn
}

output "ecs_task_role_arn" {
  description = "ARN of the ECS task role"
  value       = aws_iam_role.ecs_task_role.arn
}

output "ecs_task_execution_role_id" {
  description = "ID of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution_role.id
}

output "api_gateway_role_arn" {
  description = "ARN of the API Gateway role"
  value       = aws_iam_role.api_gateway_role.arn
}

output "api_gateway_role_name" {
  description = "Name of the API Gateway role"
  value       = aws_iam_role.api_gateway_role.name
}

output "create_job_role_arn" {
  description = "ARN of the create-job Lambda role"
  value       = aws_iam_role.create_job_role.arn
}

output "job_progress_role_arn" {
  description = "ARN of the job-progress Lambda role"
  value       = aws_iam_role.job_progress_role.arn
}

output "overall_progress_role_arn" {
  description = "ARN of the overall-progress Lambda role"
  value       = aws_iam_role.overall_progress_role.arn
}

output "get_results_role_arn" {
  description = "ARN of the get-results Lambda role"
  value       = aws_iam_role.get_results_role.arn
}

output "get_presigned_url_role_arn" {
  description = "ARN of the get-presigned-url Lambda role"
  value       = aws_iam_role.get_presigned_url_role.arn
}

output "update_results_role_arn" {
  description = "ARN of the update-results Lambda role"
  value       = aws_iam_role.update_results_role.arn
}
