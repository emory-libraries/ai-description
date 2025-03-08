# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# modules/api_gateway/main.tf

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

#----------------------------------------------
# REST API Definition
#----------------------------------------------
resource "aws_api_gateway_rest_api" "api" {
  name        = "${var.deployment_prefix}-rest-api"
  description = "REST API for Image Captioning Assistant"

  endpoint_configuration {
    types = ["EDGE"]
  }

  binary_media_types = [
    "multipart/form-data",
    "application/octet-stream"
  ]
}

#----------------------------------------------
# API Base Resource
#----------------------------------------------
resource "aws_api_gateway_resource" "api_base" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "api"
}

#----------------------------------------------
# Root Path Files
#----------------------------------------------
locals {
  root_files = ["favicon.ico", "manifest.json", "robots.txt", "asset-manifest.json"]
}

resource "aws_api_gateway_resource" "root_files" {
  for_each    = toset(local.root_files)
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = each.value
}

resource "aws_api_gateway_method" "root_files_method" {
  for_each      = toset(local.root_files)
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.root_files[each.value].id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root_files_integration" {
  for_each    = toset(local.root_files)
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.root_files[each.value].id
  http_method = aws_api_gateway_method.root_files_method[each.value].http_method

  type                    = "AWS"
  integration_http_method = "GET"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:s3:path/${var.website_bucket_name}/${each.value}"
  credentials             = var.api_gateway_role_arn
}

resource "aws_api_gateway_method_response" "root_files_method_response" {
  for_each    = toset(local.root_files)
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.root_files[each.value].id
  http_method = aws_api_gateway_method.root_files_method[each.value].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  depends_on = [
    aws_api_gateway_method.root_files_method,
    aws_api_gateway_integration.root_files_integration
  ]
}

resource "aws_api_gateway_integration_response" "root_files_integration_response" {
  for_each    = toset(local.root_files)
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.root_files[each.value].id
  http_method = aws_api_gateway_method.root_files_method[each.value].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = "integration.response.header.Content-Type"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_method_response.root_files_method_response
  ]
}

#----------------------------------------------
# Root Path Integration
#----------------------------------------------
resource "aws_api_gateway_method" "root_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_rest_api.api.root_resource_id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "root_s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.root_method.http_method

  type                    = "AWS"
  integration_http_method = "GET"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:s3:path/${var.website_bucket_name}/index.html"
  credentials             = var.api_gateway_role_arn

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "root_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.root_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "root_s3_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_rest_api.api.root_resource_id
  http_method = aws_api_gateway_method.root_method.http_method
  status_code = aws_api_gateway_method_response.root_method_response.status_code

  response_parameters = {
    "method.response.header.Content-Type"                = "integration.response.header.Content-Type"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
}

#----------------------------------------------
# Static Files Resource (Catch-All)
#----------------------------------------------
resource "aws_api_gateway_resource" "static_files" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "static_files_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.static_files.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.proxy" = true
  }
}

resource "aws_api_gateway_integration" "static_files_s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.static_files.id
  http_method = aws_api_gateway_method.static_files_method.http_method

  type                    = "AWS"
  integration_http_method = "GET"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:s3:path/${var.website_bucket_name}/index.html"
  credentials             = var.api_gateway_role_arn

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "static_files_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.static_files.id
  http_method = aws_api_gateway_method.static_files_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "static_files_s3_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.static_files.id
  http_method = aws_api_gateway_method.static_files_method.http_method
  status_code = aws_api_gateway_method_response.static_files_method_response.status_code

  response_parameters = {
    "method.response.header.Content-Type"                = "integration.response.header.Content-Type"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }
}

#----------------------------------------------
# Static Assets Resources
#----------------------------------------------
resource "aws_api_gateway_resource" "static_assets" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "static"
}

resource "aws_api_gateway_resource" "static_assets_files" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.static_assets.id
  path_part   = "{asset+}"
}

resource "aws_api_gateway_method" "static_assets_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.static_assets_files.id
  http_method   = "GET"
  authorization = "NONE"

  request_parameters = {
    "method.request.path.asset" = true
  }
}

resource "aws_api_gateway_integration" "static_assets_s3_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.static_assets_files.id
  http_method = aws_api_gateway_method.static_assets_method.http_method

  type                    = "AWS"
  integration_http_method = "GET"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:s3:path/${var.website_bucket_name}/static/{asset}"
  credentials             = var.api_gateway_role_arn

  request_parameters = {
    "integration.request.path.asset" = "method.request.path.asset"
  }
}

resource "aws_api_gateway_method_response" "static_assets_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.static_assets_files.id
  http_method = aws_api_gateway_method.static_assets_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  depends_on = [
    aws_api_gateway_integration.static_assets_s3_integration
  ]
}

resource "aws_api_gateway_integration_response" "static_assets_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.static_assets_files.id
  http_method = aws_api_gateway_method.static_assets_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = "integration.response.header.Content-Type"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_method_response.static_assets_method_response
  ]
}

#----------------------------------------------
# env.js Resource
#----------------------------------------------

resource "aws_api_gateway_resource" "env_js" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "env.js"
}

resource "aws_api_gateway_method" "env_js_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.env_js.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "env_js_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.env_js.id
  http_method = aws_api_gateway_method.env_js_method.http_method

  type                    = "AWS"
  integration_http_method = "GET"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:s3:path/${var.website_bucket_name}/env.js"
  credentials             = var.api_gateway_role_arn
}

resource "aws_api_gateway_method_response" "env_js_method_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.env_js.id
  http_method = aws_api_gateway_method.env_js_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = true
    "method.response.header.Access-Control-Allow-Origin" = true
  }

  depends_on = [
    aws_api_gateway_method.env_js_method,
    aws_api_gateway_integration.env_js_integration
  ]
}

resource "aws_api_gateway_integration_response" "env_js_integration_response" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.env_js.id
  http_method = aws_api_gateway_method.env_js_method.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Content-Type"                = "'application/javascript'"
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_integration.env_js_integration,
    aws_api_gateway_method_response.env_js_method_response
  ]
}
#----------------------------------------------
# JWT Authorizer
#----------------------------------------------
resource "aws_api_gateway_authorizer" "jwt_authorizer" {
  name                             = "jwt-authorizer"
  rest_api_id                      = aws_api_gateway_rest_api.api.id
  authorizer_uri                   = var.lambda_invoke_arns["authorize"]
  authorizer_credentials           = var.api_gateway_role_arn
  type                             = "TOKEN"
  identity_source                  = "method.request.header.Authorization"
  authorizer_result_ttl_in_seconds = 0
}

#----------------------------------------------
# API Resource Definitions
#----------------------------------------------
locals {
  base_resources = {
    "log_in" = {
      path_part = "log_in"
      methods = {
        "POST" = var.lambda_function_arns["log_in"]
      }
    }
    "create_job" = {
      path_part = "create_job"
      methods = {
        "POST" = var.lambda_function_arns["create_job"]
      }
    }
    "job_progress" = {
      path_part = "job_progress"
      methods = {
        "GET" = var.lambda_function_arns["job_progress"]
      }
    }
    "presigned_url" = {
      path_part = "presigned_url"
      methods = {
        "GET" = var.lambda_function_arns["get_presigned_url"]
      }
    }
    "overall_progress" = {
      path_part = "overall_progress"
      methods = {
        "GET" = var.lambda_function_arns["overall_progress"]
      }
    }
    "results" = {
      path_part = "results"
      methods = {
        "GET" = var.lambda_function_arns["get_results"]
        "PUT" = var.lambda_function_arns["update_results"]
      }
    }
  }
}

resource "aws_api_gateway_resource" "base_resources" {
  for_each    = local.base_resources
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.api_base.id
  path_part   = each.value.path_part
}

#----------------------------------------------
# API Methods
#----------------------------------------------
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
  authorization = each.value.resource_key == "log_in" ? "NONE" : "CUSTOM"
  authorizer_id = each.value.resource_key == "log_in" ? null : aws_api_gateway_authorizer.jwt_authorizer.id
}

#----------------------------------------------
# CORS Configuration
#----------------------------------------------
resource "aws_api_gateway_method" "options_method" {
  for_each      = local.base_resources
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.base_resources[each.key].id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options_integration" {
  for_each    = local.base_resources
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.base_resources[each.key].id
  http_method = aws_api_gateway_method.options_method[each.key].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }

  depends_on = [aws_api_gateway_method.options_method]
}

resource "aws_api_gateway_method_response" "options_200" {
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

  depends_on = [aws_api_gateway_method.options_method]
}

resource "aws_api_gateway_integration_response" "options_integration_response" {
  for_each    = local.base_resources
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.base_resources[each.key].id
  http_method = aws_api_gateway_method.options_method[each.key].http_method
  status_code = aws_api_gateway_method_response.options_200[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,x-request-timestamp,X-Request-Timestamp'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [
    aws_api_gateway_method_response.options_200,
    aws_api_gateway_integration.options_integration
  ]
}

resource "aws_api_gateway_method_response" "method_response_200" {
  for_each = {
    for entry in flatten([
      for k, v in local.base_resources : [
        for method, lambda in v.methods : {
          key          = "${k}_${method}"
          resource_key = k
          method       = method
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

  depends_on = [aws_api_gateway_method.api_methods]
}

#----------------------------------------------
# Lambda Permissions & Integrations
#----------------------------------------------
resource "aws_lambda_permission" "api_lambda_permissions" {
  for_each = {
    for entry in flatten([
      for k, v in local.base_resources : [
        for method, lambda in v.methods : {
          key    = "${k}_${method}"
          method = method
          lambda = lambda
          path   = k
        }
      ]
    ]) : entry.key => entry
  }
  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = each.value.lambda
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_integration" "api_integrations" {
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

  depends_on = [
    aws_api_gateway_method.api_methods,
    aws_lambda_permission.api_lambda_permissions
  ]
}

resource "aws_api_gateway_integration_response" "api_integration_response" {
  for_each    = aws_api_gateway_integration.api_integrations
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = each.value.resource_id
  http_method = each.value.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  depends_on = [
    aws_api_gateway_method_response.method_response_200,
    aws_api_gateway_integration.api_integrations
  ]
}

#----------------------------------------------
# Deployment & Stage
#----------------------------------------------
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode({
      base_resources      = values(aws_api_gateway_resource.base_resources)[*].id,
      methods             = values(aws_api_gateway_method.api_methods)[*].id,
      integrations        = values(aws_api_gateway_integration.api_integrations)[*].id,
      options             = values(aws_api_gateway_method.options_method)[*].id,
      options_integration = values(aws_api_gateway_integration.options_integration)[*].id,
      method_responses    = values(aws_api_gateway_method_response.method_response_200)[*].id,
      options_responses   = values(aws_api_gateway_method_response.options_200)[*].id,
      root_method         = aws_api_gateway_method.root_method.id,
      root_integration    = aws_api_gateway_integration.root_s3_integration.id,
      static_files        = aws_api_gateway_resource.static_files.id,
      static_files_method = aws_api_gateway_method.static_files_method.id,
      static_integration  = aws_api_gateway_integration.static_files_s3_integration.id,
      static_assets       = aws_api_gateway_resource.static_assets.id,
      static_assets_files = aws_api_gateway_resource.static_assets_files.id,
      root_files          = values(aws_api_gateway_resource.root_files)[*].id
    }))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_method.api_methods,
    aws_api_gateway_integration.api_integrations,
    aws_api_gateway_method_response.method_response_200,
    aws_api_gateway_integration_response.api_integration_response,
    aws_api_gateway_integration.options_integration,
    aws_api_gateway_method.options_method,
    aws_api_gateway_method_response.options_200,
    aws_api_gateway_integration_response.options_integration_response,
    aws_api_gateway_method.root_method,
    aws_api_gateway_integration.root_s3_integration,
    aws_api_gateway_method.static_files_method,
    aws_api_gateway_integration.static_files_s3_integration,
    aws_api_gateway_method.static_assets_method,
    aws_api_gateway_integration.static_assets_s3_integration,
    aws_api_gateway_method_response.static_assets_method_response,
    aws_api_gateway_integration_response.static_assets_integration_response,
    aws_api_gateway_method.root_files_method,
    aws_api_gateway_integration.root_files_integration,
    aws_api_gateway_method_response.root_files_method_response,
    aws_api_gateway_integration_response.root_files_integration_response
  ]
}

resource "aws_cloudwatch_log_group" "api_gateway_logs" {
  name              = "/aws/apigateway/${aws_api_gateway_rest_api.api.name}"
  retention_in_days = 30
}

resource "aws_api_gateway_stage" "api_stage" {
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.deployment_stage

  # Disable the stage name in URLs
  variables = {
    "basePath" = var.deployment_stage
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway_logs.arn
    format = jsonencode({
      requestId               = "$context.requestId"
      sourceIp                = "$context.identity.sourceIp"
      requestTime             = "$context.requestTime"
      protocol                = "$context.protocol"
      httpMethod              = "$context.httpMethod"
      resourcePath            = "$context.resourcePath"
      routeKey                = "$context.routeKey"
      status                  = "$context.status"
      responseLength          = "$context.responseLength"
      integrationErrorMessage = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api_stage.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    data_trace_enabled     = true
    throttling_rate_limit  = 100
    throttling_burst_limit = 50
  }
}

resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = var.api_gateway_role_arn
}
