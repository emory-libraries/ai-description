# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# ECS outputs

output "cluster_name" {
  description = "The name of the ECS cluster"
  value       = aws_ecs_cluster.cluster.name
}

output "task_definition_arn" {
  description = "The ARN of the ECS task definition"
  value       = aws_ecs_task_definition.task.arn
}

output "security_group_ids" {
  description = "List of security group IDs for ECS tasks"
  value       = [aws_security_group.ecs_service_sg.id]
}

output "subnet_ids" {
  description = "List of subnet IDs for ECS tasks"
  value       = var.subnet_ids
}
