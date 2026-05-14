########################################
# ECS
########################################

resource "aws_ecs_cluster" "apollo" {
  name = local.name_prefix

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecs-cluster"
  })
}

resource "aws_cloudwatch_log_group" "apollo_migration" {
  name              = "/ecs/${local.name_prefix}-migration"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-migration-logs"
  })
}

resource "aws_cloudwatch_log_group" "apollo_web" {
  name              = "/ecs/${local.name_prefix}-web"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web-logs"
  })
}

resource "aws_cloudwatch_log_group" "apollo_worker" {
  name              = "/ecs/${local.name_prefix}-worker"
  retention_in_days = 14

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-worker-logs"
  })
}

locals {
  apollo_common_environment = [
    {
      name  = "PREFERRED_URL_SCHEME"
      value = "https"
    },
    {
      name  = "DATABASE_HOSTNAME"
      value = aws_db_instance.apollo.address
    },
    {
      name  = "DATABASE_NAME"
      value = aws_db_instance.apollo.db_name
    },
    {
      name  = "DATABASE_USERNAME"
      value = var.db_username
    },
    {
      name  = "REDIS_HOSTNAME"
      value = aws_elasticache_replication_group.apollo.primary_endpoint_address
    },
    {
      name  = "REDIS_DATABASE"
      value = "0"
    },
    {
      name  = "ATTACHMENTS_USE_S3"
      value = "true"
    },
    {
      name  = "AWS_DEFAULT_BUCKET"
      value = aws_s3_bucket.apollo_attachments.bucket
    },
    {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    },
    {
      name  = "TIMEZONE"
      value = var.timezone
    },
    {
      name  = "DEFAULT_EMAIL_SENDER"
      value = var.default_email_sender
    },
    {
      name  = "FLASK_ENV"
      value = "production"
    },
    {
      name  = "FLASK_APP"
      value = "apollo.runner"
    }
  ]
}

resource "aws_ecs_task_definition" "apollo_migration" {
  family                   = "${local.name_prefix}-migration"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.migration_task_cpu)
  memory                   = tostring(var.migration_task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.apollo_task.arn

  container_definitions = jsonencode([
    {
      name      = "apollo-migration"
      image     = var.apollo_image_uri
      essential = true
      command   = ["flask", "db", "upgrade"]

      environment = local.apollo_common_environment

      secrets = [
        {
          name      = "SECRET_KEY"
          valueFrom = aws_secretsmanager_secret_version.apollo_secret_key.arn
        },
        {
          name      = "DATABASE_PASSWORD"
          valueFrom = aws_secretsmanager_secret_version.apollo_db_password.arn
        },
        {
          name      = "AWS_ACCESS_KEY_ID"
          valueFrom = aws_secretsmanager_secret_version.apollo_aws_access_key_id.arn
        },
        {
          name      = "AWS_SECRET_ACCESS_KEY"
          valueFrom = aws_secretsmanager_secret_version.apollo_aws_secret_access_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.apollo_migration.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-migration-taskdef"
  })
}

resource "aws_ecs_task_definition" "apollo_web" {
  family                   = "${local.name_prefix}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.web_task_cpu)
  memory                   = tostring(var.web_task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.apollo_task.arn

  container_definitions = jsonencode([
    {
      name      = "apollo-web"
      image     = var.apollo_image_uri
      essential = true
      command   = ["gunicorn", "-c", "gunicorn.py", "apollo.runner"]

      portMappings = [
        {
          containerPort = var.app_port
          hostPort      = var.app_port
          protocol      = "tcp"
        }
      ]

      mountPoints = [
        {
          sourceVolume  = "apollo-uploads"
          containerPath = "/app/uploads"
          readOnly      = false
        }
      ]

      environment = local.apollo_common_environment

      secrets = [
        {
          name      = "SECRET_KEY"
          valueFrom = aws_secretsmanager_secret_version.apollo_secret_key.arn
        },
        {
          name      = "DATABASE_PASSWORD"
          valueFrom = aws_secretsmanager_secret_version.apollo_db_password.arn
        },
        {
          name      = "AWS_ACCESS_KEY_ID"
          valueFrom = aws_secretsmanager_secret_version.apollo_aws_access_key_id.arn
        },
        {
          name      = "AWS_SECRET_ACCESS_KEY"
          valueFrom = aws_secretsmanager_secret_version.apollo_aws_secret_access_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.apollo_web.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  volume {
    name = "apollo-uploads"

    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.apollo_uploads.id
      transit_encryption = "ENABLED"

      authorization_config {
        access_point_id = aws_efs_access_point.apollo_uploads.id
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web-taskdef"
  })
}

resource "aws_ecs_task_definition" "apollo_worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.worker_task_cpu)
  memory                   = tostring(var.worker_task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.apollo_task.arn

  container_definitions = jsonencode([
    {
      name      = "apollo-worker"
      image     = var.apollo_image_uri
      essential = true
      command   = ["celery", "--app=apollo.runner", "worker", "--beat", "--loglevel=WARNING", "--concurrency=2", "--without-gossip", "--without-mingle", "--optimization=fair"]

      environment = local.apollo_common_environment

      mountPoints = [
        {
          sourceVolume  = "apollo-uploads"
          containerPath = "/app/uploads"
          readOnly      = false
        }
      ]

      secrets = [
        {
          name      = "SECRET_KEY"
          valueFrom = aws_secretsmanager_secret_version.apollo_secret_key.arn
        },
        {
          name      = "DATABASE_PASSWORD"
          valueFrom = aws_secretsmanager_secret_version.apollo_db_password.arn
        },
        {
          name      = "AWS_ACCESS_KEY_ID"
          valueFrom = aws_secretsmanager_secret_version.apollo_aws_access_key_id.arn
        },
        {
          name      = "AWS_SECRET_ACCESS_KEY"
          valueFrom = aws_secretsmanager_secret_version.apollo_aws_secret_access_key.arn
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.apollo_worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  volume {
    name = "apollo-uploads"

    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.apollo_uploads.id
      transit_encryption = "ENABLED"

      authorization_config {
        access_point_id = aws_efs_access_point.apollo_uploads.id
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-worker-taskdef"
  })
}

resource "aws_ecs_service" "apollo_web" {
  name            = "${local.name_prefix}-web"
  cluster         = aws_ecs_cluster.apollo.id
  task_definition = aws_ecs_task_definition.apollo_web.arn
  desired_count   = var.web_desired_count
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 50
  deployment_maximum_percent         = 200

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.web.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.apollo_web.arn
    container_name   = "apollo-web"
    container_port   = var.app_port
  }

  depends_on = [
    aws_lb_listener.apollo_https
  ]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web-service"
  })
}

resource "aws_ecs_service" "apollo_worker" {
  name            = "${local.name_prefix}-worker"
  cluster         = aws_ecs_cluster.apollo.id
  task_definition = aws_ecs_task_definition.apollo_worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-worker-service"
  })
}