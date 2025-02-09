# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# API Gateway module

data "aws_region" "current" {}

# Create a REST API
resource "aws_api_gateway_rest_api" "api" {
  name        = "ai-description-${var.deployment_name}"
  description = "REST API for Item Mapping POC"

  binary_media_types = [
    "multipart/form-data",
    "application/octet-stream"
  ]
}

# Define resources and methods
locals {
  # Base resources (no parent dependencies)
  base_resources = {
    "create_job" = {
      path_part = "create_job"
      methods = {
        "POST" = var.lambda["create_job"]
      }
    }
    "job_progress" = {
      path_part = "job_progress"
      methods = {
        "GET" = var.lambda["job_progress"]
      }
    }
    "results" = {
      path_part = "results"
      methods = {
        "GET" = var.lambda["results"]
      }
    }
  }
}

# Create base resources
resource "aws_api_gateway_resource" "base_resources" {
  for_each    = local.base_resources
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = each.value.path_part
}


# Create methods for actual endpoints
resource "aws_api_gateway_method" "api_methods" {
  for_each = {
    for entry in flatten([
      for k, v in local.base_resources : [
        for method, lambda in v.methods : {
          key          = "${k}_${method}"
          resource_key = k
          method       = method
          lambda       = lambda
        }
      ]
    ]) : entry.key => entry
  }
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.base_resources[each.value.resource_key].id
  http_method   = each.value.method
  authorization = "NONE"
}

# Create OPTIONS method for CORS
resource "aws_api_gateway_method" "options_method" {
  for_each      = local.base_resources
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.base_resources[each.key].id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

# Create integration for OPTIONS method
resource "aws_api_gateway_integration" "options_integration" {
  depends_on = [aws_api_gateway_method.options_method]

  for_each    = local.base_resources
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.base_resources[each.key].id
  http_method = aws_api_gateway_method.options_method[each.key].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

# Create method response for OPTIONS
resource "aws_api_gateway_method_response" "options_200" {
  depends_on = [aws_api_gateway_method.options_method]

  for_each    = local.base_resources
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.base_resources[each.key].id
  http_method = aws_api_gateway_method.options_method[each.key].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

# Create integration response for OPTIONS
resource "aws_api_gateway_integration_response" "options_integration_response" {
  depends_on = [
    aws_api_gateway_method_response.options_200,
    aws_api_gateway_integration.options_integration
  ]

  for_each    = local.base_resources
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.base_resources[each.key].id
  http_method = aws_api_gateway_method.options_method[each.key].http_method
  status_code = aws_api_gateway_method_response.options_200[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Add method responses for actual endpoints
resource "aws_api_gateway_method_response" "method_response_200" {
  depends_on = [aws_api_gateway_method.api_methods]

  for_each = {
    for entry in flatten([
      for k, v in local.base_resources : [
        for method, lambda in v.methods : {
          key          = "${k}_${method}"
          resource_key = k
          method       = method
          lambda       = lambda
        }
      ]
    ]) : entry.key => entry
  }
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.base_resources[each.value.resource_key].id
  http_method = each.value.method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

# Lambda permissions
resource "aws_lambda_permission" "api_lambda_permissions" {
  for_each = {
    for entry in flatten([
      for k, v in local.base_resources : [
        for method, lambda in v.methods : {
          key    = "${k}_${method}"
          method = method
          lambda = lambda
        }
      ]
    ]) : entry.key => entry
  }
  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.lambda
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/${each.value.method}/*"
}

# Lambda integrations
resource "aws_api_gateway_integration" "api_integrations" {
  depends_on = [
    aws_api_gateway_method.api_methods,
    aws_lambda_permission.api_lambda_permissions
  ]

  for_each = {
    for entry in flatten([
      for k, v in local.base_resources : [
        for method, lambda in v.methods : {
          key          = "${k}_${method}"
          resource_key = k
          method       = method
          lambda       = lambda
        }
      ]
    ]) : entry.key => entry
  }
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.base_resources[each.value.resource_key].id
  http_method             = each.value.method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${each.value.lambda}/invocations"
}

# Integration responses for actual endpoints
resource "aws_api_gateway_integration_response" "api_integration_response" {
  depends_on = [
    aws_api_gateway_method_response.method_response_200,
    aws_api_gateway_integration.api_integrations
  ]

  for_each    = aws_api_gateway_integration.api_integrations
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
}

# Deployment
resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on = [
    aws_api_gateway_method.api_methods,
    aws_api_gateway_integration.api_integrations,
    aws_api_gateway_method_response.method_response_200,
    aws_api_gateway_integration_response.api_integration_response,
    aws_api_gateway_integration.options_integration,
    aws_api_gateway_method.options_method,
    aws_api_gateway_method_response.options_200,
    aws_api_gateway_integration_response.options_integration_response
  ]

  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode({
      base_resources      = values(aws_api_gateway_resource.base_resources)[*].id,
      methods             = values(aws_api_gateway_method.api_methods)[*].id,
      integrations        = values(aws_api_gateway_integration.api_integrations)[*].id,
      options             = values(aws_api_gateway_method.options_method)[*].id,
      options_integration = values(aws_api_gateway_integration.options_integration)[*].id,
      method_responses    = values(aws_api_gateway_method_response.method_response_200)[*].id,
      options_responses   = values(aws_api_gateway_method_response.options_200)[*].id
    }))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Separate stage resource
resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.stage_name
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api_stage.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled = true
    logging_level   = "INFO"
  }
}

resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = var.cloudwatch_role_arn
}