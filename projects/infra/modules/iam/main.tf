# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# modules/iam/main.tf

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Create Job Lambda Role
resource "aws_iam_role" "create_job_role" {
  name = "${var.deployment_prefix}-create-job-role"
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

# Create Job Policy
resource "aws_iam_policy" "create_job_policy" {
  name = "${var.deployment_prefix}-create-job-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
        ]
        Resource = [var.sqs_works_queue_arn]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          var.uploads_bucket_arn,
          "${var.uploads_bucket_arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [var.works_table_arn]
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

resource "aws_iam_role_policy_attachment" "create_job_attachment" {
  role       = aws_iam_role.create_job_role.name
  policy_arn = aws_iam_policy.create_job_policy.arn
}

# Job Progress Lambda Role
resource "aws_iam_role" "job_progress_role" {
  name = "${var.deployment_prefix}-job-progress-role"
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

# Job Progress Policy
resource "aws_iam_policy" "job_progress_policy" {
  name = "${var.deployment_prefix}-job-progress-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [var.works_table_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "job_progress_attachment" {
  role       = aws_iam_role.job_progress_role.name
  policy_arn = aws_iam_policy.job_progress_policy.arn
}

# Overall Progress Lambda Role
resource "aws_iam_role" "overall_progress_role" {
  name = "${var.deployment_prefix}-overall-progress-role"
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

# Overall Progress Policy
resource "aws_iam_policy" "overall_progress_policy" {
  name = "${var.deployment_prefix}-overall-progress-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
        Action = [
          "sqs:ReceiveMessage",
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
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [var.works_table_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "overall_progress_attachment" {
  role       = aws_iam_role.overall_progress_role.name
  policy_arn = aws_iam_policy.overall_progress_policy.arn
}

# Get Results Lambda Role
resource "aws_iam_role" "get_results_role" {
  name = "${var.deployment_prefix}-get-results-role"
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

# Get Results Policy
resource "aws_iam_policy" "get_results_policy" {
  name = "${var.deployment_prefix}-get-results-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [var.works_table_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "get_results_attachment" {
  role       = aws_iam_role.get_results_role.name
  policy_arn = aws_iam_policy.get_results_policy.arn
}

# Get Presigned URL Lambda Role
resource "aws_iam_role" "get_presigned_url_role" {
  name = "${var.deployment_prefix}-get-presigned-url-role"
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

# Get Presigned URL Policy
resource "aws_iam_policy" "get_presigned_url_policy" {
  name = "${var.deployment_prefix}-get-presigned-url-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          var.uploads_bucket_arn,
          "${var.uploads_bucket_arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "get_presigned_url_attachment" {
  role       = aws_iam_role.get_presigned_url_role.name
  policy_arn = aws_iam_policy.get_presigned_url_policy.arn
}

# Update Results Lambda Role
resource "aws_iam_role" "update_results_role" {
  name = "${var.deployment_prefix}-update-results-role"
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

# Update Results Policy
resource "aws_iam_policy" "update_results_policy" {
  name = "${var.deployment_prefix}-update-results-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [var.works_table_arn]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "update_results_attachment" {
  role       = aws_iam_role.update_results_role.name
  policy_arn = aws_iam_policy.update_results_policy.arn
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
          "s3:ListBucket",
        ]
        Resource = [
          "${var.uploads_bucket_arn}",
          "${var.uploads_bucket_arn}/*",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
        ]
        Resource = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]
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
        ],
        "Resource" : ["*"] # Must be wildcard
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "ecs:DescribeClusters",
          "ecs:ListClusters",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ],
        "Resource" : ["*"]
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
resource "aws_iam_role" "api_gateway_role" {
  name = "${var.deployment_prefix}-api-gateway-role"

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

# API Gateway Policy
resource "aws_iam_policy" "website_bucket_access_policy" {
  name = "${var.deployment_prefix}-website-bucket-access-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.website_bucket_arn,
          "${var.website_bucket_arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "invoke_lambda_policy" {
  name = "${var.deployment_prefix}-invoke-lambda-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:*"
      }
    ]
  })
}
# API Gateway Role-Policy Attachments
resource "aws_iam_role_policy_attachment" "api_gateway_website_policy" {
  role       = aws_iam_role.api_gateway_role.name
  policy_arn = aws_iam_policy.website_bucket_access_policy.arn
}
resource "aws_iam_role_policy_attachment" "api_gateway_lambda_policy" {
  role       = aws_iam_role.api_gateway_role.name
  policy_arn = aws_iam_policy.invoke_lambda_policy.arn
}
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_policy" {
  role       = aws_iam_role.api_gateway_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}
resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch_full_access" {
  role       = aws_iam_role.api_gateway_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# VPC Endpoint policies
resource "aws_vpc_endpoint_policy" "s3_policy" {
  count           = var.enable_vpc_endpoints ? 1 : 0
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
          "s3:ListBucket",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_vpc_endpoint_policy" "ecr_api_policy" {
  count           = var.enable_vpc_endpoints ? 1 : 0
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
  count           = var.enable_vpc_endpoints ? 1 : 0
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
