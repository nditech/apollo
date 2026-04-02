########################################
# Storage
########################################

resource "aws_s3_bucket" "apollo_attachments" {
  bucket = var.attachments_bucket_name

  tags = local.common_tags
}

resource "aws_s3_bucket_public_access_block" "apollo_attachments" {
  bucket = aws_s3_bucket.apollo_attachments.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}