# Outputs describing this specific Apollo deployment instance.
# These values expose app-facing/runtime artifacts such as task definitions, service names,
# public hostname, and secret references used by the running deployment.

output "apollo_migration_task_definition_arn" {
  description = "ARN of the Apollo migration task definition"
  value       = aws_ecs_task_definition.apollo_migration.arn
}

output "apollo_web_task_definition_arn" {
  description = "ARN of the Apollo web task definition"
  value       = aws_ecs_task_definition.apollo_web.arn
}

output "apollo_worker_task_definition_arn" {
  description = "ARN of the Apollo worker task definition"
  value       = aws_ecs_task_definition.apollo_worker.arn
}

output "apollo_secret_key_secret_arn" {
  description = "ARN of the Apollo SECRET_KEY secret"
  value       = aws_secretsmanager_secret.apollo_secret_key.arn
}

output "apollo_db_password_secret_arn" {
  description = "ARN of the Apollo database password secret"
  value       = aws_secretsmanager_secret.apollo_db_password.arn
}

output "apollo_aws_access_key_id_secret_arn" {
  description = "ARN of the Apollo AWS access key ID secret"
  value       = aws_secretsmanager_secret.apollo_aws_access_key_id.arn
}

output "apollo_aws_secret_access_key_secret_arn" {
  description = "ARN of the Apollo AWS secret access key secret"
  value       = aws_secretsmanager_secret.apollo_aws_secret_access_key.arn
}

output "apollo_web_service_name" {
  description = "Name of the Apollo web ECS service"
  value       = aws_ecs_service.apollo_web.name
}

output "apollo_worker_service_name" {
  description = "Name of the Apollo worker ECS service"
  value       = aws_ecs_service.apollo_worker.name
}

output "apollo_public_hostname" {
  description = "Public hostname for Apollo"
  value       = aws_route53_record.apollo.fqdn
}