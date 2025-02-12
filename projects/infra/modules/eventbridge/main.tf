# EventBridge module

# Alarm for SQS queue not empty
resource "aws_cloudwatch_metric_alarm" "sqs_not_empty" {
  alarm_name          = "${var.deployment_prefix}-sqs-not-empty"
  alarm_description   = "Alarm when SQS queue is not empty"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  comparison_operator = "GreaterThanThreshold"
  threshold           = "0"
  statistic           = "Sum"
  evaluation_periods  = "1"
  period              = "60"
  namespace           = "AWS/SQS"
  dimensions = {
    QueueName = var.sqs_works_queue_name
  }
}

# Alarm for ECS cluster idle
resource "aws_cloudwatch_metric_alarm" "ecs_running" {
  alarm_name          = "${var.deployment_prefix}-ecs-running"
  alarm_description   = "Alarm when ECS cluster has a running task"
  metric_name         = "TaskCount"
  comparison_operator = "GreaterThanThreshold"
  threshold           = "0"
  statistic           = "Sum"
  evaluation_periods  = "1"
  period              = "60"
  namespace           = "ECS/ContainerInsights"
  dimensions = {
    ClusterName = var.ecs_cluster_name
  }
}

# Composite alarm
resource "aws_cloudwatch_composite_alarm" "sqs_not_empty_and_ecs_idle" {
  alarm_name        = "${var.deployment_prefix}-sqs-not-empty-and-ecs-idle"
  alarm_description = "Composite alarm that triggers when SQS queue is not empty and ECS cluster has no running tasks"

  alarm_rule = "ALARM(${aws_cloudwatch_metric_alarm.sqs_not_empty.alarm_name}) AND NOT ALARM(${aws_cloudwatch_metric_alarm.ecs_running.alarm_name})"
}

# EventBridge rule
resource "aws_cloudwatch_event_rule" "sqs_not_empty_and_ecs_idle" {
  name        = "${var.deployment_prefix}-sqs-not-empty-and-ecs-idle"
  description = "Trigger when SQS queue is not empty and ECS cluster has no running tasks"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      "state" : {
        "value" : ["ALARM"]
      },
      "alarmName" : [
        "${aws_cloudwatch_composite_alarm.sqs_not_empty_and_ecs_idle.alarm_name}"
      ]
    }
  })
}

# EventBridge target
resource "aws_cloudwatch_event_target" "trigger_lambda" {
  rule      = aws_cloudwatch_event_rule.sqs_not_empty_and_ecs_idle.name
  target_id = "TriggerLambda"
  arn       = var.run_ecs_task_lambda_arn
}

# Lambda permission
resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = var.run_ecs_task_lambda_arn
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.sqs_not_empty_and_ecs_idle.arn
}