output "queue_url" {
  description = "The URL of the SQS work queue"
  value       = aws_sqs_queue.work_queue.id
}

output "queue_arn" {
  description = "The ARN of the created Amazon SQS queue"
  value       = aws_sqs_queue.work_queue.arn
}