# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# Secrets Manager main module

resource "random_password" "jwt_secret" {
  count   = var.generate_random_secret ? 1 : 0
  length  = 32
  special = true
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = var.secret_name
  description             = var.description
  recovery_window_in_days = var.recovery_window_in_days
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.generate_random_secret ? random_password.jwt_secret[0].result : var.provided_secret_key
}