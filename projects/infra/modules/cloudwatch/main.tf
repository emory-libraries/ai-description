# CloudWatch module

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/ai-description-poc/logs-${var.deployment_name}"
  retention_in_days = 30
}
