output "name_prefix" {
  description = "Common prefix for resource names"
  value       = local.name_prefix
}

output "attachments_bucket_name" {
  description = "S3 bucket name for Apollo attachments"
  value       = aws_s3_bucket.apollo_attachments.bucket
}

output "vpc_id" {
  description = "ID of the Apollo VPC"
  value       = aws_vpc.apollo.id
}

output "vpc_cidr" {
  description = "CIDR block of the Apollo VPC"
  value       = aws_vpc.apollo.cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_app_subnet_ids" {
  description = "IDs of the private app subnets"
  value       = aws_subnet.private_app[*].id
}

output "private_data_subnet_ids" {
  description = "IDs of the private data subnets"
  value       = aws_subnet.private_data[*].id
}

output "internet_gateway_id" {
  description = "ID of the Apollo internet gateway"
  value       = aws_internet_gateway.apollo.id
}

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "alb_security_group_id" {
  description = "ID of the ALB security group"
  value       = aws_security_group.alb.id
}

output "web_security_group_id" {
  description = "ID of the web task security group"
  value       = aws_security_group.web.id
}

output "worker_security_group_id" {
  description = "ID of the worker task security group"
  value       = aws_security_group.worker.id
}

output "rds_security_group_id" {
  description = "ID of the RDS security group"
  value       = aws_security_group.rds.id
}

output "redis_security_group_id" {
  description = "ID of the Redis security group"
  value       = aws_security_group.redis.id
}

output "db_instance_endpoint" {
  description = "Endpoint of the Apollo PostgreSQL instance"
  value       = aws_db_instance.apollo.endpoint
}

output "db_instance_address" {
  description = "Address of the Apollo PostgreSQL instance"
  value       = aws_db_instance.apollo.address
}

output "db_name" {
  description = "Database name for Apollo"
  value       = aws_db_instance.apollo.db_name
}