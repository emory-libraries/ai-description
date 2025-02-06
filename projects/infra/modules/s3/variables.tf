# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# S3 variables

variable "start_ecs_task_lambda_arn" {
  description = "ARN of the Lambda function to start ECS tasks"
  type        = string
}

variable "deployment_name" {
  description = "Unique name of deployment"
  type        = string
}
