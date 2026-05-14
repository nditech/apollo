########################################
# Redis
########################################

resource "aws_elasticache_subnet_group" "apollo" {
  name       = "${local.name_prefix}-redis-subnet-group"
  subnet_ids = aws_subnet.private_data[*].id

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-redis-subnet-group"
  })
}

resource "aws_elasticache_replication_group" "apollo" {
  replication_group_id = "${local.name_prefix}-redis"
  description          = "Apollo Redis replication group"
  engine               = "redis"
  engine_version       = var.redis_engine_version
  node_type            = var.redis_node_type
  port                 = var.redis_port

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
