########################################
# ECR
########################################

resource "aws_ecr_repository" "apollo" {
  name = "apollo"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ecr"
  })
}