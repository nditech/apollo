variable "aws_region" {
  type        = string
  description = "AWS region for Terraform backend resources"
  default     = "us-east-1"
}

variable "state_bucket_name" {
  type        = string
  description = "S3 bucket name for Terraform remote state"
  default     = "cdoten-apollo-terraform-state"
}
