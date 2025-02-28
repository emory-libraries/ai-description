# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# IAM module
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Base Lambda Role
resource "aws_iam_role" "base_lambda_role" {
  name = "${var.deployment_prefix}-base-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Base Lambda Policy (common permissions)
resource "aws_iam_policy" "base_lambda_policy" {
  name = "${var.deployment_prefix}-base-lambda-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:logs:*:*:*",
          "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/*"
        ]
      }
    ]
  })
}

# Service-Specific Policy
resource "aws_iam_policy" "service_lambda_policy" {
  name = "${var.deployment_prefix}-service-lambda-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          var.sqs_works_queue_arn,
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
        ]
        Resource = [
          var.uploads_bucket_arn,
          "${var.uploads_bucket_arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan",
        ]
        Resource = [
          "arn:aws:dynamodb:*:*:table/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "ecs:ListTasks",
          "ecs:RunTask"
        ]
        Resource = [
          "arn:aws:ecs:*:*:cluster/*",
          "arn:aws:ecs:*:*:container-instance/*",
          "arn:aws:ecs:*:*:task-definition/*",
          "arn:aws:ecs:*:*:task/*",
        ]
      },
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = [
          aws_iam_role.ecs_task_execution_role.arn,
          aws_iam_role.ecs_task_role.arn
        ]
      }
    ]
  })
}

# Lambda Policy Attachments
resource "aws_iam_role_policy_attachment" "base_lambda_base_policy" {
  role       = aws_iam_role.base_lambda_role.name
  policy_arn = aws_iam_policy.base_lambda_policy.arn
}

resource "aws_iam_role_policy_attachment" "base_lambda_service_policy" {
  role       = aws_iam_role.base_lambda_role.name
  policy_arn = aws_iam_policy.service_lambda_policy.arn
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_task_execution_role" {
  name                  = "${var.deployment_prefix}-ecs-task-execution-role"
  force_detach_policies = true
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# Attach base ECS execution policy
resource "aws_iam_role_policy_attachment" "ecs_task_execution_policy_attach" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_ecr_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.deployment_prefix}-ecs-task-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# ECS Task Policy
resource "aws_iam_policy" "ecs_task_policy" {
  name        = "${var.deployment_prefix}-ecs-task-policy"
  path        = "/"
  description = "IAM policy for ECS tasks"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          var.sqs_works_queue_arn,
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ]
        Resource = [var.works_table_arn]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
        ]
        Resource = [
          "${var.uploads_bucket_arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = ["arn:aws:logs:*:*:*"]
      },
      {
        Effect   = "Allow"
        Action   = ["bedrock:InvokeModel"]
        Resource = ["*"] # Any Bedrock model can be invoked
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "cloudwatch:PutMetricData",
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics",
          "ecs:DescribeClusters",
          "ecs:ListClusters",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ],
        "Resource" : "*"
      }
    ]
  })
}

# ECS Task Role-Policy Attachment
resource "aws_iam_role_policy_attachment" "ecs_task_policy_attachment" {
  policy_arn = aws_iam_policy.ecs_task_policy.arn
  role       = aws_iam_role.ecs_task_role.name
}

# API Gateway Role
resource "aws_iam_role" "api_gateway_cloudwatch_role" {
  name = "${var.deployment_prefix}-api-gateway-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })
}

# API Gateway Role-Policy Attachment
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
  role       = aws_iam_role.api_gateway_cloudwatch_role.name
}

# VPC Endpoint policies
resource "aws_vpc_endpoint_policy" "s3_policy" {
  count           = var.vpc_s3_endpoint_id != null ? 1 : 0
  vpc_endpoint_id = var.vpc_s3_endpoint_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowS3Access"
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_vpc_endpoint_policy" "ecr_api_policy" {
  count           = var.vpc_ecr_api_endpoint_id != null ? 1 : 0
  vpc_endpoint_id = var.vpc_ecr_api_endpoint_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowECRAPI"
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_vpc_endpoint_policy" "ecr_dkr_policy" {
  count           = var.vpc_ecr_dkr_endpoint_id != null ? 1 : 0
  vpc_endpoint_id = var.vpc_ecr_dkr_endpoint_id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowAll"
        Effect    = "Allow"
        Principal = "*"
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = "*"
      }
    ]
  })
}
