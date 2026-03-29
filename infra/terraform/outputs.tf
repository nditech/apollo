output "name_prefix" {
  description = "Common prefix for resource names"
  value       = local.name_prefix
}

output "attachments_bucket_name" {
  description = "S3 bucket name for Apollo attachments"
  value       = aws_s3_bucket.apollo_attachments.bucket
}
