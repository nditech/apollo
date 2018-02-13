# -*- coding: utf-8 -*-
from apollo.dal.service import Service
from apollo.users import models


class UserService(Service):
    __model__ = models.User

    def get_permissions_cache(self, instance):
        if not self._isinstance(instance):
            return None

        deployment = instance.deployment

        # if this is an admin user, set all role
        # and user permissions
        if instance.is_admin():
            return {
                'user': '__all__',
                'role': '__all__'
            }

        perm_cache = {}
        # load up role permissions
        role_perms = models.RolePermission.query.with_entities(
            models.RolePermission.perm_name).join(models.Role.users).filter(
            models.Role.users.contains(instance),
            models.RolePermission.deployment == deployment).all()

        # load up user perms
        user_perms = models.UserPermission.query.with_entities(
            models.UserResourcePermission.perm_name).filter_by(
                user_id=instance.id, deployment_id=deployment.id).all()

        perm_cache['role_perms'] = role_perms
        perm_cache['user_perms'] = user_perms

        return perm_cache


class UserUploadService(Service):
    __model__ = models.UserUpload
