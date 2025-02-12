variable "deployment_name" {
  description = "Unique name of deployment"
  type        = string
}

variable "sqs_works_queue_name" {
  description = "Name of the SQS works queue"
  type        = string
}

variable "run_ecs_task_lambda_arn" {
  description = "ARN of the Lambda function to start ECS tasks"
  type        = string
}
