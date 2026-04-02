########################################
# Security groups
########################################

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