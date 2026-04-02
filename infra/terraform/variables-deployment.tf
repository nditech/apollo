# Deployment-specific inputs for this particular Apollo instance.
# These variables capture app/runtime choices such as hostname, image, task sizing,
# secrets, email, timezone, and other settings that are expected to vary per deployment.

variable "db_password" {
  type        = string
  description = "Master password for the Apollo database"
  sensitive   = true
}

variable "apollo_image_uri" {
  type        = string
  description = "Apollo container image URI in ECR"
  default     = "592016371171.dkr.ecr.us-east-1.amazonaws.com/apollo:2026-03-31.2"
}

variable "ecs_task_cpu" {
  type        = number
  description = "CPU units for Apollo ECS tasks"
  default     = 512
}

variable "ecs_task_memory" {
  type        = number
  description = "Memory (MiB) for Apollo ECS tasks"
  default     = 1024
}

variable "secret_key" {
  type        = string
  description = "Flask secret key for Apollo"
  sensitive   = true
}

variable "timezone" {
  type        = string
  description = "Default timezone for Apollo"
  default     = "America/New_York"
}

variable "default_email_sender" {
  type        = string
  description = "Default email sender for Apollo"
  default     = "witness@cocitizen.com"
}

variable "apollo_certificate_arn" {
  type        = string
  description = "ACM certificate ARN for the Apollo public hostname"
  default     = "arn:aws:acm:us-east-1:592016371171:certificate/4e27f9a4-6087-4ac1-ab39-b76731d7a450"
}

variable "apollo_hostname" {
  type        = string
  description = "Public hostname for Apollo"
  default     = "witness.cocitizen.com"
}

variable "health_check_path" {
  type        = string
  description = "HTTP path used by the ALB target group health check"
  default     = "/"
}

variable "aws_access_key_id" {
  type        = string
  description = "AWS access key ID used by Apollo for S3 attachments"
  sensitive   = true
}

variable "aws_secret_access_key" {
  type        = string
  description = "AWS secret access key used by Apollo for S3 attachments"
  sensitive   = true
}