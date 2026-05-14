########################################
# Database
########################################

resource "aws_db_subnet_group" "apollo" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = aws_subnet.private_data[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-db-subnet-group"
  })
}

resource "aws_db_instance" "apollo" {
  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = var.db_engine_version
  instance_class = var.db_instance_class

  allocated_storage = var.db_allocated_storage
  storage_type      = "gp3"
  db_name           = var.db_name
  username          = var.db_username
  password          = var.db_password
  port              = 5432

  db_subnet_group_name   = aws_db_subnet_group.apollo.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false
  multi_az            = false

  # Set apply_immediately to make any changes upon "terraform apply" 
  # instead of waiting for the maintenance window.
  # For routine production-like DB changes, leave this as false.
  apply_immediately = false

  skip_final_snapshot = true
  deletion_protection = false

  backup_retention_period    = 7
  auto_minor_version_upgrade = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-postgres"
  })
}