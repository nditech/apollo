########################################
# IAM
########################################

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
