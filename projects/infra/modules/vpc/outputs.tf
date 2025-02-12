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

output "vpc_s3_endpoint_id" {
  description = "The ID of the VPC's S3 endpoint"
  value       = aws_vpc_endpoint.s3.id
}

output "vpc_ecr_api_endpoint_id" {
  description = "The ID of the VPC's ECR API endpoint"
  value       = aws_vpc_endpoint.ecr_api.id
}

output "vpc_ecr_dkr_endpoint_id" {
  description = "The ID of the VPC's ECR DKR endpoint"
  value       = aws_vpc_endpoint.ecr_dkr.id
}

output "ecs_security_group_id" {
  description = "ID of ECS Security Group"
  value       = aws_security_group.ecs_service_sg.id
}

output "vpc_endpoints_security_group_id" {
  description = "ID of VPC Endpoints Security Group"
  value       = aws_security_group.vpc_endpoints.id
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
    s3      = aws_vpc_endpoint.s3.id
    ecr_api = aws_vpc_endpoint.ecr_api.id
    ecr_dkr = aws_vpc_endpoint.ecr_dkr.id
    logs    = aws_vpc_endpoint.logs.id
  }
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = data.aws_availability_zones.available.names
}