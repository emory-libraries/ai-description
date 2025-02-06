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

output "public_route_table_ids" {
  description = "List of IDs of public route tables"
  value = local.create_vpc ? [aws_route_table.public[0].id] : (
    data.aws_route_tables.public[0].ids
  )
}

output "private_route_table_ids" {
  description = "List of IDs of private route tables"
  value = local.create_vpc ? [aws_route_table.private[0].id] : (
    data.aws_route_tables.private[0].ids
  )
}
