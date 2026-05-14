########################################
# DNS / Load Balancing
########################################

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