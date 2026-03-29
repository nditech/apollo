variable "aws_region" {
  type        = string
  description = "AWS region for Apollo infrastructure"
  default     = "us-east-1"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming"
  default     = "apollo"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "dev"
}
