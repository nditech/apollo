# Outputs describing the underlying AWS/Apollo foundation created by this Terraform root.
# These are designed to be general, not specific to any certain implementation.
# These values expose the reusable environment building blocks such as network, storage,
# database, Redis, load balancer, cluster, and IAM identities.

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

output "redis_primary_endpoint_address" {
  description = "Primary endpoint address of the Apollo Redis replication group"
  value       = aws_elasticache_replication_group.apollo.primary_endpoint_address
}

output "redis_port" {
  description = "Port of the Apollo Redis replication group"
  value       = aws_elasticache_replication_group.apollo.port
}

output "ecr_repository_url" {
  description = "URL of the Apollo ECR repository"
  value       = aws_ecr_repository.apollo.repository_url
}

output "ecs_cluster_name" {
  description = "Name of the Apollo ECS cluster"
  value       = aws_ecs_cluster.apollo.name
}

output "ecs_cluster_arn" {
  description = "ARN of the Apollo ECS cluster"
  value       = aws_ecs_cluster.apollo.arn
}

output "ecs_task_execution_role_arn" {
  description = "ARN of the ECS task execution role"
  value       = aws_iam_role.ecs_task_execution.arn
}

output "apollo_task_role_arn" {
  description = "ARN of the Apollo task role"
  value       = aws_iam_role.apollo_task.arn
}

output "apollo_alb_dns_name" {
  description = "DNS name of the Apollo load balancer"
  value       = aws_lb.apollo.dns_name
}

output "apollo_alb_zone_id" {
  description = "Route 53 zone ID of the Apollo load balancer"
  value       = aws_lb.apollo.zone_id
}

output "apollo_s3_iam_username" {
  description = "IAM username for Apollo S3 attachment access"
  value       = aws_iam_user.apollo_s3.name
}

output "apollo_s3_iam_user_arn" {
  description = "ARN of the Apollo S3 IAM user"
  value       = aws_iam_user.apollo_s3.arn
}