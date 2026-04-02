locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = "cdoten"
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

resource "aws_vpc" "apollo" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-vpc"
  })
}

resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)

  vpc_id                  = aws_vpc.apollo.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-${count.index + 1}"
    Tier = "public"
  })
}

resource "aws_subnet" "private_app" {
  count = length(var.private_app_subnet_cidrs)

  vpc_id            = aws_vpc.apollo.id
  cidr_block        = var.private_app_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-app-${count.index + 1}"
    Tier = "private-app"
  })
}

resource "aws_subnet" "private_data" {
  count = length(var.private_data_subnet_cidrs)

  vpc_id            = aws_vpc.apollo.id
  cidr_block        = var.private_data_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-private-data-${count.index + 1}"
    Tier = "private-data"
  })
}

resource "aws_internet_gateway" "apollo" {
  vpc_id = aws_vpc.apollo.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-igw"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.apollo.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-public-rt"
    Tier = "public"
  })
}

resource "aws_route" "public_internet_access" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.apollo.id
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}


resource "aws_security_group" "alb" {
  name        = "${local.name_prefix}-alb-sg"
  description = "Security group for the Apollo load balancer"
  vpc_id      = aws_vpc.apollo.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "alb_https_in" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "Allow HTTPS from the internet"
}

resource "aws_vpc_security_group_egress_rule" "alb_all_out" {
  security_group_id = aws_security_group.alb.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic"
}

resource "aws_security_group" "web" {
  name        = "${local.name_prefix}-web-sg"
  description = "Security group for Apollo web tasks"
  vpc_id      = aws_vpc.apollo.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "web_from_alb" {
  security_group_id            = aws_security_group.web.id
  referenced_security_group_id = aws_security_group.alb.id
  from_port                    = var.app_port
  to_port                      = var.app_port
  ip_protocol                  = "tcp"
  description                  = "Allow app traffic from the ALB"
}

resource "aws_vpc_security_group_egress_rule" "web_all_out" {
  security_group_id = aws_security_group.web.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic"
}

resource "aws_security_group" "worker" {
  name        = "${local.name_prefix}-worker-sg"
  description = "Security group for Apollo worker tasks"
  vpc_id      = aws_vpc.apollo.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-worker-sg"
  })
}

resource "aws_vpc_security_group_egress_rule" "worker_all_out" {
  security_group_id = aws_security_group.worker.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic"
}

resource "aws_security_group" "rds" {
  name        = "${local.name_prefix}-rds-sg"
  description = "Security group for Apollo PostgreSQL"
  vpc_id      = aws_vpc.apollo.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-rds-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_web" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.web.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  description                  = "Allow PostgreSQL from web tasks"
}

resource "aws_vpc_security_group_ingress_rule" "rds_from_worker" {
  security_group_id            = aws_security_group.rds.id
  referenced_security_group_id = aws_security_group.worker.id
  from_port                    = 5432
  to_port                      = 5432
  ip_protocol                  = "tcp"
  description                  = "Allow PostgreSQL from worker tasks"
}

resource "aws_vpc_security_group_egress_rule" "rds_all_out" {
  security_group_id = aws_security_group.rds.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic"
}

resource "aws_security_group" "redis" {
  name        = "${local.name_prefix}-redis-sg"
  description = "Security group for Apollo Redis"
  vpc_id      = aws_vpc.apollo.id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "redis_from_web" {
  security_group_id            = aws_security_group.redis.id
  referenced_security_group_id = aws_security_group.web.id
  from_port                    = 6379
  to_port                      = 6379
  ip_protocol                  = "tcp"
  description                  = "Allow Redis from web tasks"
}

resource "aws_vpc_security_group_ingress_rule" "redis_from_worker" {
  security_group_id            = aws_security_group.redis.id
  referenced_security_group_id = aws_security_group.worker.id
  from_port                    = 6379
  to_port                      = 6379
  ip_protocol                  = "tcp"
  description                  = "Allow Redis from worker tasks"
}

resource "aws_vpc_security_group_egress_rule" "redis_all_out" {
  security_group_id = aws_security_group.redis.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all outbound traffic"
}

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

  allocated_storage     = var.db_allocated_storage
  storage_type          = "gp3"
  db_name               = var.db_name
  username              = var.db_username
  password              = var.db_password
  port                  = 5432

  db_subnet_group_name   = aws_db_subnet_group.apollo.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false
  multi_az            = false

  skip_final_snapshot = true
  deletion_protection = false

  backup_retention_period = 7

  auto_minor_version_upgrade = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-postgres"
  })
}

resource "aws_elasticache_subnet_group" "apollo" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = aws_subnet.private_data[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-subnet-group"
  })
}

resource "aws_elasticache_replication_group" "apollo" {
  replication_group_id       = "${local.name_prefix}-redis"
  description                = "Apollo Redis replication group"
  engine                     = "redis"
  engine_version             = var.redis_engine_version
  node_type                  = var.redis_node_type
  port                       = var.redis_port

  num_cache_clusters         = 1
  automatic_failover_enabled = false
  multi_az_enabled           = false

  subnet_group_name  = aws_elasticache_subnet_group.apollo.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis"
  })
}

resource "aws_ecr_repository" "apollo" {
  name = "apollo"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecr"
  })
}

resource "aws_ecs_cluster" "apollo" {
  name = local.name_prefix

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecs-cluster"
  })
}


data "aws_iam_policy_document" "ecs_tasks_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${local.name_prefix}-ecs-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecs-task-execution-role"
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_managed" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "apollo_task" {
  name               = "${local.name_prefix}-apollo-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume_role.json

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-apollo-task-role"
  })
}

data "aws_iam_policy_document" "apollo_task_s3" {
  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.apollo_attachments.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "${aws_s3_bucket.apollo_attachments.arn}/*"
    ]
  }
}

resource "aws_iam_role_policy" "apollo_task_s3" {
  name   = "${local.name_prefix}-apollo-task-s3"
  role   = aws_iam_role.apollo_task.id
  policy = data.aws_iam_policy_document.apollo_task_s3.json
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
  cpu                      = tostring(var.ecs_task_cpu)
  memory                   = tostring(var.ecs_task_memory)
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
  cpu                      = tostring(var.ecs_task_cpu)
  memory                   = tostring(var.ecs_task_memory)
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

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web-taskdef"
  })
}

resource "aws_ecs_task_definition" "apollo_worker" {
  family                   = "${local.name_prefix}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.ecs_task_cpu)
  memory                   = tostring(var.ecs_task_memory)
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.apollo_task.arn

  container_definitions = jsonencode([
    {
      name      = "apollo-worker"
      image     = var.apollo_image_uri
      essential = true
      command   = ["celery", "--app=apollo.runner", "worker", "--beat", "--loglevel=WARNING", "--concurrency=2", "--without-gossip", "--without-mingle", "--optimization=fair"]

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
          awslogs-group         = aws_cloudwatch_log_group.apollo_worker.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-worker-taskdef"
  })
}

resource "aws_secretsmanager_secret" "apollo_secret_key" {
  name = "${local.name_prefix}/apollo/secret-key"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-apollo-secret-key"
  })
}

resource "aws_secretsmanager_secret_version" "apollo_secret_key" {
  secret_id     = aws_secretsmanager_secret.apollo_secret_key.id
  secret_string = var.secret_key
}

resource "aws_secretsmanager_secret" "apollo_db_password" {
  name = "${local.name_prefix}/apollo/db-password"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-apollo-db-password"
  })
}

resource "aws_secretsmanager_secret_version" "apollo_db_password" {
  secret_id     = aws_secretsmanager_secret.apollo_db_password.id
  secret_string = var.db_password
}

resource "aws_lb" "apollo" {
  name               = "${local.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb"
  })
}

resource "aws_lb_target_group" "apollo_web" {
  name        = "${local.name_prefix}-web-tg"
  port        = var.app_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.apollo.id

  health_check {
    enabled             = true
    path                = var.health_check_path
    port                = "traffic-port"
    protocol            = "HTTP"
    matcher             = "200-399"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 5
    interval            = 30
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-web-tg"
  })
}

resource "aws_lb_listener" "apollo_https" {
  load_balancer_arn = aws_lb.apollo.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = var.apollo_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.apollo_web.arn
  }
}

resource "aws_lb_listener" "apollo_http_redirect" {
  load_balancer_arn = aws_lb.apollo.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_ecs_service" "apollo_web" {
  name            = "${local.name_prefix}-web"
  cluster         = aws_ecs_cluster.apollo.id
  task_definition = aws_ecs_task_definition.apollo_web.arn
  desired_count   = 1
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
  desired_count   = 1
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

data "aws_route53_zone" "cocitizen" {
  name         = "cocitizen.com"
  private_zone = false
}

resource "aws_route53_record" "apollo" {
  zone_id = data.aws_route53_zone.cocitizen.zone_id
  name    = var.apollo_hostname
  type    = "A"

  alias {
    name                   = aws_lb.apollo.dns_name
    zone_id                = aws_lb.apollo.zone_id
    evaluate_target_health = true
  }
}

data "aws_iam_policy_document" "ecs_task_execution_secrets" {
  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = [
      aws_secretsmanager_secret.apollo_secret_key.arn,
      aws_secretsmanager_secret.apollo_db_password.arn,
      aws_secretsmanager_secret.apollo_aws_access_key_id.arn,
      aws_secretsmanager_secret.apollo_aws_secret_access_key.arn
    ]
  }
}

resource "aws_iam_role_policy" "ecs_task_execution_secrets" {
  name   = "${local.name_prefix}-ecs-task-execution-secrets"
  role   = aws_iam_role.ecs_task_execution.id
  policy = data.aws_iam_policy_document.ecs_task_execution_secrets.json
}

resource "aws_secretsmanager_secret" "apollo_aws_access_key_id" {
  name = "${local.name_prefix}/apollo/aws-access-key-id"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-apollo-aws-access-key-id"
  })
}

resource "aws_secretsmanager_secret_version" "apollo_aws_access_key_id" {
  secret_id     = aws_secretsmanager_secret.apollo_aws_access_key_id.id
  secret_string = var.aws_access_key_id
}

resource "aws_secretsmanager_secret" "apollo_aws_secret_access_key" {
  name = "${local.name_prefix}/apollo/aws-secret-access-key"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-apollo-aws-secret-access-key"
  })
}

resource "aws_secretsmanager_secret_version" "apollo_aws_secret_access_key" {
  secret_id     = aws_secretsmanager_secret.apollo_aws_secret_access_key.id
  secret_string = var.aws_secret_access_key
}

resource "aws_iam_user" "apollo_s3" {
  name = var.apollo_s3_iam_username

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-apollo-s3-user"
  })
}

data "aws_iam_policy_document" "apollo_s3_user_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:ListAllMyBuckets"
    ]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:ListBucket"
    ]
    resources = [
      aws_s3_bucket.apollo_attachments.arn
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject"
    ]
    resources = [
      "${aws_s3_bucket.apollo_attachments.arn}/*"
    ]
  }
}

resource "aws_iam_user_policy" "apollo_s3_user_policy" {
  name   = "${local.name_prefix}-apollo-s3-user-policy"
  user   = aws_iam_user.apollo_s3.name
  policy = data.aws_iam_policy_document.apollo_s3_user_policy.json
}