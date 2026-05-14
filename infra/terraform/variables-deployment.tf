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
  default     = "592016371171.dkr.ecr.us-east-1.amazonaws.com/apollo:2026-04-30.1"
}

variable "migration_task_cpu" {
  type        = number
  description = "CPU units for the one-off Apollo migration ECS task. 1024 = 1 vCPU."
  default     = 512
}

variable "migration_task_memory" {
  type        = number
  description = "Memory in MiB for the one-off Apollo migration ECS task."
  default     = 1024
}

variable "web_desired_count" {
  type        = number
  description = "Number of Apollo web tasks to run. Use 2+ for pilot/live use so one unhealthy or restarting task does not take down the site."
  default     = 1
}

variable "web_task_cpu" {
  type        = number
  description = "CPU units for each Apollo web ECS task. 1024 = 1 vCPU. Pilot recommendation: 1024."
  default     = 512
}

variable "web_task_memory" {
  type        = number
  description = "Memory in MiB for each Apollo web ECS task. Pilot recommendation: 4096."
  default     = 1024
}

variable "worker_desired_count" {
  type        = number
  description = "Number of Apollo worker tasks. Keep at 1 while the worker command also runs Celery beat, unless beat is split into its own service."
  default     = 1
}

variable "worker_task_cpu" {
  type        = number
  description = "CPU units for the Apollo worker ECS task. 1024 = 1 vCPU. Pilot recommendation: 1024."
  default     = 512
}

variable "worker_task_memory" {
  type        = number
  description = "Memory in MiB for the Apollo worker ECS task. Pilot recommendation: 4096 for imports, generation tasks, and other long-running jobs."
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