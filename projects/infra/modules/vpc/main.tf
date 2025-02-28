# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# VPC module

locals {
  create_vpc = var.vpc_id == ""
  vpc_id     = local.create_vpc ? aws_vpc.main[0].id : data.aws_vpc.existing[0].id
}

data "aws_region" "current" {}

data "aws_vpc" "existing" {
  count = local.create_vpc ? 0 : 1
  id    = var.vpc_id
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_subnets" "public" {
  count = local.create_vpc ? 0 : 1

  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  tags = {
    Tier = "Public"
  }
}

data "aws_subnets" "private" {
  count = local.create_vpc ? 0 : 1

  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }

  tags = {
    Tier = "Private"
  }
}

data "aws_route_tables" "private" {
  count  = local.create_vpc ? 0 : 1
  vpc_id = var.vpc_id

  tags = {
    Tier = "Private"
  }
}

# Create VPC if needed
resource "aws_vpc" "main" {
  count = local.create_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.deployment_prefix}-vpc"
  }
}

# Private subnets
resource "aws_subnet" "private" {
  count = local.create_vpc ? length(var.azs) : 0

  vpc_id            = local.vpc_id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.deployment_prefix}-private-${count.index + 1}"
    Tier = "Private"
  }
}

# Public subnets
resource "aws_subnet" "public" {
  count = local.create_vpc ? length(var.azs) : 0

  vpc_id            = local.vpc_id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + length(var.azs))
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.deployment_prefix}-public-${count.index + 1}"
    Tier = "Public"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = local.create_vpc ? 1 : 0

  vpc_id = local.vpc_id

  tags = {
    Name = "${var.deployment_prefix}-igw"
  }
}

# Route Tables
resource "aws_route_table" "private" {
  count = local.create_vpc ? length(var.azs) : 0

  vpc_id = local.vpc_id

  tags = {
    Name = "${var.deployment_prefix}-private-rt-${count.index + 1}"
    Tier = "Private"
  }
}

resource "aws_route_table" "public" {
  count = local.create_vpc ? length(var.azs) : 0

  vpc_id = local.vpc_id

  tags = {
    Name = "${var.deployment_prefix}-public-rt-${count.index + 1}"
    Tier = "Public"
  }
}

# Internet Gateway route for public subnets
resource "aws_route" "public_igw" {
  count = local.create_vpc ? length(var.azs) : 0

  route_table_id         = aws_route_table.public[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main[0].id
}

# Route Table Associations
resource "aws_route_table_association" "private" {
  count = local.create_vpc ? length(var.azs) : length(data.aws_subnets.private[0].ids)

  subnet_id      = local.create_vpc ? aws_subnet.private[count.index].id : data.aws_subnets.private[0].ids[count.index]
  route_table_id = local.create_vpc ? aws_route_table.private[count.index].id : data.aws_route_tables.private[0].ids[count.index % length(data.aws_route_tables.private[0].ids)]
}

resource "aws_route_table_association" "public" {
  count = local.create_vpc ? length(var.azs) : length(data.aws_subnets.public[0].ids)

  subnet_id      = local.create_vpc ? aws_subnet.public[count.index].id : data.aws_subnets.public[0].ids[count.index]
  route_table_id = local.create_vpc ? aws_route_table.public[count.index].id : data.aws_route_tables.public[0].ids[count.index % length(data.aws_route_tables.public[0].ids)]
}

# Security Groups
resource "aws_security_group" "ecs_service_sg" {
  name        = "${var.deployment_prefix}-ecs-service-sg"
  description = "Security group for ECS tasks"
  vpc_id      = local.vpc_id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow ECS tasks to egress on port 443 (HTTPS)"
  }

  tags = {
    Name = "${var.deployment_prefix}-ecs-service-sg"
  }
}

resource "aws_security_group" "vpc_endpoints_sg" {
  name        = "${var.deployment_prefix}-vpc-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = local.vpc_id

  ingress {
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_service_sg.id]
    description     = "Allow HTTPS from ECS tasks"
  }

  tags = {
    Name = "${var.deployment_prefix}-vpc-endpoints-sg"
  }
}

# VPC Endpoints
resource "aws_vpc_endpoint" "s3" {
  count             = var.enable_vpc_endpoints ? 1 : 0
  vpc_id            = local.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = local.create_vpc ? aws_route_table.private[*].id : data.aws_route_tables.private[0].ids

  tags = {
    Name = "${var.deployment_prefix}-s3-endpoint"
  }
}

resource "aws_vpc_endpoint" "dynamodb" {
  count             = var.enable_vpc_endpoints ? 1 : 0
  vpc_id            = local.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = local.create_vpc ? aws_route_table.private[*].id : data.aws_route_tables.private[0].ids

  tags = {
    Name = "${var.deployment_prefix}-dynamodb-endpoint"
  }
}

resource "aws_vpc_endpoint" "ecr_api" {
  count               = var.enable_vpc_endpoints ? 1 : 0
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = local.create_vpc ? aws_subnet.private[*].id : data.aws_subnets.private[0].ids
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]

  tags = {
    Name = "${var.deployment_prefix}-ecr-api-endpoint"
  }
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  count               = var.enable_vpc_endpoints ? 1 : 0
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = local.create_vpc ? aws_subnet.private[*].id : data.aws_subnets.private[0].ids
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]

  tags = {
    Name = "${var.deployment_prefix}-ecr-dkr-endpoint"
  }
}

resource "aws_vpc_endpoint" "sqs" {
  count               = var.enable_vpc_endpoints ? 1 : 0
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.sqs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = local.create_vpc ? aws_subnet.private[*].id : data.aws_subnets.private[0].ids
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]

  tags = {
    Name = "${var.deployment_prefix}-sqs-endpoint"
  }
}

resource "aws_vpc_endpoint" "logs" {
  count               = var.enable_vpc_endpoints ? 1 : 0
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.logs"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = local.create_vpc ? aws_subnet.private[*].id : data.aws_subnets.private[0].ids
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]

  tags = {
    Name = "${var.deployment_prefix}-logs-endpoint"
  }
}

resource "aws_vpc_endpoint" "cloudwatch" {
  count               = var.enable_vpc_endpoints ? 1 : 0
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.monitoring"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = local.create_vpc ? aws_subnet.private[*].id : data.aws_subnets.private[0].ids
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]

  tags = {
    Name = "${var.deployment_prefix}-cloudwatch-endpoint"
  }
}

resource "aws_vpc_endpoint" "bedrock" {
  count               = var.enable_vpc_endpoints ? 1 : 0
  vpc_id              = local.vpc_id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = local.create_vpc ? aws_subnet.private[*].id : data.aws_subnets.private[0].ids
  security_group_ids  = [aws_security_group.vpc_endpoints_sg.id]

  tags = {
    Name = "${var.deployment_prefix}-bedrock-runtime-endpoint"
  }
}
