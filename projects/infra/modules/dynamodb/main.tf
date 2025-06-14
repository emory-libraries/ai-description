# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# DynamoDB module

resource "aws_dynamodb_table" "works" {
  name         = "${var.deployment_prefix}-works-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_name"
  range_key    = "work_id"
  attribute {
    name = "job_name"
    type = "S"
  }

  attribute {
    name = "work_id"
    type = "S"
  }
  point_in_time_recovery {
    enabled = true
  }
}
