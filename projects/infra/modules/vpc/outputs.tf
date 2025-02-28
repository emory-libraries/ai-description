# Copyright © Amazon.com and Affiliates: This deliverable is considered Developed Content as defined in the AWS Service
# Terms and the SOW between the parties dated 2025.

# VPC outputs

output "vpc_id" {
  description = "The ID of the VPC"
  value       = local.vpc_id
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = local.create_vpc ? aws_vpc.main[0].cidr_block : data.aws_vpc.existing[0].cidr_block
}

output "public_subnet_ids" {
  description = "List of IDs of public subnets"
  value = local.create_vpc ? aws_subnet.public[*].id : (
    data.aws_subnets.public[0].ids
  )
}

output "private_subnet_ids" {
  description = "List of IDs of private subnets"
  value = local.create_vpc ? aws_subnet.private[*].id : (
    data.aws_subnets.private[0].ids
  )
}

output "ecs_security_group_id" {
  description = "ID of ECS Security Group"
  value       = aws_security_group.ecs_service_sg.id
}

output "vpc_endpoints_security_group_id" {
  description = "ID of VPC Endpoints Security Group"
  value       = aws_security_group.vpc_endpoints_sg.id
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables"
  value       = local.create_vpc ? [aws_route_table.private[0].id] : []
}

output "public_route_table_ids" {
  description = "List of IDs of public route tables"
  value       = local.create_vpc ? [aws_route_table.public[0].id] : []
}

output "vpc_endpoint_ids" {
  description = "Map of VPC Endpoint IDs"
  value = {
    s3         = var.enable_vpc_endpoints ? aws_vpc_endpoint.s3[0].id : null
    ecr_api    = var.enable_vpc_endpoints ? aws_vpc_endpoint.ecr_api[0].id : null
    ecr_dkr    = var.enable_vpc_endpoints ? aws_vpc_endpoint.ecr_dkr[0].id : null
    logs       = var.enable_vpc_endpoints ? aws_vpc_endpoint.logs[0].id : null
    sqs        = var.enable_vpc_endpoints ? aws_vpc_endpoint.sqs[0].id : null
    cloudwatch = var.enable_vpc_endpoints ? aws_vpc_endpoint.cloudwatch[0].id : null
    bedrock    = var.enable_vpc_endpoints ? aws_vpc_endpoint.bedrock[0].id : null
  }
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = data.aws_availability_zones.available.names
}
