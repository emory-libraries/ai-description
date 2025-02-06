# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# VPC module

locals {
  create_vpc = var.vpc_id == ""
  vpc_id     = local.create_vpc ? aws_vpc.main[0].id : data.aws_vpc.existing[0].id
}

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

data "aws_route_tables" "public" {
  count  = local.create_vpc ? 0 : 1
  vpc_id = var.vpc_id

  filter {
    name   = "tag:Tier"
    values = ["Public"]
  }
}

data "aws_route_tables" "private" {
  count  = local.create_vpc ? 0 : 1
  vpc_id = var.vpc_id

  filter {
    name   = "tag:Tier"
    values = ["Private"]
  }
}

# Create VPC if needed
resource "aws_vpc" "main" {
  count = local.create_vpc ? 1 : 0

  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "vpc-${var.deployment_name}"
  }
}

# Private subnets
resource "aws_subnet" "private" {
  count = local.create_vpc ? length(var.azs) : 0

  vpc_id            = local.vpc_id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "private-${count.index + 1}-${var.deployment_name}"
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
    Name = "public-${count.index + 1}-${var.deployment_name}"
    Tier = "Public"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  count = local.create_vpc ? 1 : 0

  vpc_id = local.vpc_id

  tags = {
    Name = "igw-${var.deployment_name}"
  }
}

# NAT Gateway
resource "aws_eip" "nat" {
  count  = local.create_vpc ? 1 : 0
  domain = "vpc"
}

resource "aws_nat_gateway" "main" {
  count = local.create_vpc ? 1 : 0

  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = {
    Name = "nat-${var.deployment_name}"
  }
}

# Route Tables
resource "aws_route_table" "private" {
  count = local.create_vpc ? 1 : 0

  vpc_id = local.vpc_id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = {
    Name = "private-rt-${var.deployment_name}"
    Tier = "Private"
  }
}

resource "aws_route_table" "public" {
  count = local.create_vpc ? 1 : 0

  vpc_id = local.vpc_id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = {
    Name = "public-rt-${var.deployment_name}"
    Tier = "Public"
  }
}

# Route Table Associations
resource "aws_route_table_association" "private" {
  count = local.create_vpc ? length(var.azs) : 0

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

resource "aws_route_table_association" "public" {
  count = local.create_vpc ? length(var.azs) : 0

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}
