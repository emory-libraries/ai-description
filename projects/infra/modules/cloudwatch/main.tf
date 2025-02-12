# CloudWatch module

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "${var.deployment_prefix_logs}/logs"
  retention_in_days = 30
}
