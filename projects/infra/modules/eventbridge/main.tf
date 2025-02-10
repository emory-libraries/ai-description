resource "aws_cloudwatch_metric_alarm" "queue_not_empty" {
  alarm_name          = "${var.deployment_name}-sqs-queue-not-empty"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "10"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This alarm triggers when there are messages in the queue"

  dimensions = {
    QueueName = var.sqs_works_queue_name
  }
}

resource "aws_cloudwatch_event_rule" "sqs_not_empty" {
  name        = "${var.deployment_name}-sqs-not-empty"
  description = "Trigger when SQS queue is not empty"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    resources   = [aws_cloudwatch_metric_alarm.queue_not_empty.arn]
    detail = {
      state = {
        value = ["ALARM"]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.sqs_not_empty.name
  target_id = "TriggerLambda"
  arn       = var.run_ecs_task_lambda_arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = var.run_ecs_task_lambda_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sqs_not_empty.arn
}