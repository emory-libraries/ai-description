# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# DynamoDB module

resource "aws_dynamodb_table" "jobs" {
  name         = "jobs-table-${var.deployment_name}"
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
}
