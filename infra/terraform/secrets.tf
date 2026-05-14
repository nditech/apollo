########################################
# Secrets
########################################

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
