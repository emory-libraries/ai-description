# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# IAM outputs

output "base_lambda_role_arn" {
  description = "ARN of the base Lambda execution role"
  value       = aws_iam_role.base_lambda_role.arn
}

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

output "a2i_role_arn" {
  description = "ARN of the A2I workflow role"
  value       = aws_iam_role.a2i_role.arn
}

output "api_gateway_cloudwatch_role_arn" {
  description = "ARN of the API Gateway CloudWatch role"
  value       = aws_iam_role.api_gateway_cloudwatch_role.arn
}
