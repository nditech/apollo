########################################
# Shared uploads filesystem
########################################

resource "aws_efs_file_system" "apollo_uploads" {
  creation_token = "${local.name_prefix}-uploads"

  encrypted = true

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-uploads-efs"
  })
}

resource "aws_efs_access_point" "apollo_uploads" {
  file_system_id = aws_efs_file_system.apollo_uploads.id

  posix_user {
    uid = 1000
    gid = 1000
  }

  root_directory {
    path = "/uploads"

    creation_info {
      owner_uid   = 1000
      owner_gid   = 1000
      permissions = "0775"
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-uploads-access-point"
  })
}

resource "aws_efs_mount_target" "apollo_uploads" {
  count = length(aws_subnet.public)

  file_system_id  = aws_efs_file_system.apollo_uploads.id
  subnet_id       = aws_subnet.public[count.index].id
  security_groups = [aws_security_group.efs.id]
}
