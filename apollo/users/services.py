# -*- coding: utf-8 -*-
from apollo.core import db
from apollo.dal.models import Permission, Resource
from apollo.dal.service import Service
from apollo.frontend import permissions
from apollo.users.models import (
    Role, User, UserUpload, role_resource_permissions,
    user_resource_permissions)


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

        role_resource_perms = db.session.query(
            Resource.resource_id, Resource.resource_type).join(
                role_resource_permissions
            ).join(Role).filter(
                    Role.users.contains(instance)).all()
        perm_cache.extend(
            permissions.ItemNeed('access_resource', n[0], n[1])
            for n in role_resource_perms)

        # load up user perms
        user_perms = Permission.query.with_entities(Permission.name).filter(
            Permission.users.contains(instance)).all()
        perm_cache.extend([permissions.ActionNeed(n[0]) for n in user_perms])

        user_resource_perms = db.session.query(
            Resource.resource_id, Resource.resource_type
        ).join(user_resource_permissions).join(User).filter(
            User.id == instance.id).all()
        perm_cache.extend(
            permissions.ItemNeed('access_resource', n[0], n[1])
            for n in user_resource_perms)

        return perm_cache


class UserUploadService(Service):
    __model__ = UserUpload
