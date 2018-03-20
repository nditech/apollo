# -*- coding: utf-8 -*-
from apollo.dal.models import Permission
from apollo.dal.service import Service
from apollo.frontend import permissions
from apollo.users.models import Role, User, UserUpload


class UserService(Service):
    __model__ = User

    def get_permissions_cache(self, instance):
        if not self._isinstance(instance):
            return None

        # if this is an admin user, set all role
        # and user permissions
        if instance.is_admin():
            return [permissions.RoleNeed('admin')]

        perm_cache = []
        # load up role permissions
        role_perms = Permission.query.with_entities(Permission.name).join(
            Permission.roles).filter(Role.users.contains(instance)).all()
        perm_cache.extend([permissions.ActionNeed(n[0]) for n in role_perms])

        # load up user perms
        user_perms = Permission.query.with_entities(Permission.name).filter(
            Permission.users.contains(instance)).all()
        perm_cache.extend([permissions.ActionNeed(n[0]) for n in user_perms])

        return perm_cache


class UserUploadService(Service):
    __model__ = UserUpload
