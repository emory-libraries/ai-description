# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# SQS outputs

output "queue_url" {
  description = "The URL of the SQS work queue"
  value       = aws_sqs_queue.work_queue.id
}

output "queue_arn" {
  description = "The ARN of the created Amazon SQS queue"
  value       = aws_sqs_queue.work_queue.arn
}

output "queue_name" {
  description = "The name of the created Amazon SQS queue"
  value       = aws_sqs_queue.work_queue.name
}
