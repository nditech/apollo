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

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the Apollo VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones for Apollo infrastructure"
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_app_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private app subnets"
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "private_data_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private data subnets"
  default     = ["10.0.21.0/24", "10.0.22.0/24"]
}

variable "app_port" {
  type        = number
  description = "Port the Apollo web application listens on"
  default     = 5000
}

variable "db_name" {
  type        = string
  description = "Initial Apollo database name"
  default     = "apollo"
}

variable "db_username" {
  type        = string
  description = "Master username for the Apollo database"
  default     = "apollo_admin"
}

variable "db_password" {
  type        = string
  description = "Master password for the Apollo database"
  sensitive   = true
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class for Apollo PostgreSQL"
  default     = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type        = number
  description = "Allocated storage in GiB for the Apollo database"
  default     = 20
}

variable "db_engine_version" {
  type        = string
  description = "PostgreSQL engine version for Apollo"
  default     = "16"
}

variable "redis_node_type" {
  type        = string
  description = "ElastiCache node type for Apollo Redis"
  default     = "cache.t4g.micro"
}

variable "redis_engine_version" {
  type        = string
  description = "Redis OSS engine version for Apollo Redis"
  default     = "7.1"
}

variable "redis_port" {
  type        = number
  description = "Port for Apollo Redis"
  default     = 6379
}