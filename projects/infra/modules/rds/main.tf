# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# RDS module

data "aws_region" "current" {}

# Store DB credentials in Secrets Manager
resource "aws_secretsmanager_secret" "aurora_credentials" {
  name = "aurora-creds-${var.deployment_name}"
}

resource "aws_secretsmanager_secret_version" "aurora_credentials" {
  secret_id = aws_secretsmanager_secret.aurora_credentials.id
  secret_string = jsonencode({
    username = "dbadmin"
    password = random_password.master.result
    engine   = "postgres"
    host     = aws_rds_cluster.aurora.endpoint
    port     = 5432
    dbname   = "appdb"
  })
}

# Random password for initial DB setup
resource "random_password" "master" {
  length  = 16
  special = true
}

# Subnet group for Aurora
resource "aws_db_subnet_group" "aurora" {
  name        = "aurora-subnet-group-${var.deployment_name}"
  subnet_ids  = var.subnet_ids
  description = "Subnet group for Aurora Serverless cluster"
}

# Security group for Aurora
resource "aws_security_group" "aurora" {
  name        = "aurora-sg-${var.deployment_name}"
  description = "Security group for Aurora Serverless cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Aurora Serverless v2 Cluster
resource "aws_rds_cluster" "aurora" {
  cluster_identifier = "aurora-${var.deployment_name}"
  engine             = "aurora-postgresql"
  engine_mode        = "provisioned"
  engine_version     = "15.4"
  database_name      = "appdb"
  master_username    = "dbadmin"
  master_password    = random_password.master.result
  storage_encrypted  = true

  db_subnet_group_name   = aws_db_subnet_group.aurora.name
  vpc_security_group_ids = [aws_security_group.aurora.id]

  serverlessv2_scaling_configuration {
    max_capacity             = var.max_capacity
    min_capacity             = var.min_capacity
    seconds_until_auto_pause = var.auto_pause_seconds
  }

  skip_final_snapshot = var.skip_final_snapshot
}

# Aurora Serverless v2 Instance
resource "aws_rds_cluster_instance" "aurora" {
  cluster_identifier = aws_rds_cluster.aurora.id
  instance_class     = "db.serverless"
  engine             = aws_rds_cluster.aurora.engine
  engine_version     = aws_rds_cluster.aurora.engine_version
}
