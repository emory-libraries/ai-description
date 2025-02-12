# EventBridge variables

variable "deployment_prefix" {
  description = "Unique name of the deployment"
  type        = string
}

variable "sqs_works_queue_name" {
  description = "Name of the SQS works queue"
  type        = string
}

variable "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  type        = string
}

variable "run_ecs_task_lambda_arn" {
  description = "ARN of the Lambda function to start ECS tasks"
  type        = string
}
