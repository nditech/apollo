locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_s3_bucket" "apollo_attachments" {
  bucket = "cdoten-apollo-dev-attachments"

  tags = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "apollo_attachments" {
  bucket = aws_s3_bucket.apollo_attachments.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
