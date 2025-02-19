# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# CloudWatch module

resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "${var.deployment_prefix_logs}/logs"
  retention_in_days = 30
}
