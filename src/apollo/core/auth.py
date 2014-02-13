from __future__ import unicode_literals
from django.contrib.auth.hashers import make_password
from mongoengine import BooleanField, Document, ListField, ObjectIdField
from mongoengine import ReferenceField, StringField
from .utils import get_full_class_name


class PrincipalMixin(object):
    '''Common mixin for identities trying to access resources'''
    def add_permission(self, name, cls_or_obj):
        model_class = get_full_class_name(cls_or_obj)
        permission = Permission.objects(codename=name, model=model_class).first()

        if not permission:
            raise ValueError('Permission {} for {} does not exist'.format(
                name, model_class
            ))
        permission.principals.append(self.id)
        permission.save()

        # remove the cached permissions, so the next time they're
        # accessed, they can be refreshed
        if hasattr(self, '_perm_cache'):
            delattr(self, '_perm_cache')

    def remove_permission(self, name, cls_or_obj):
        model_class = get_full_class_name(cls_or_obj)
        permission = Permission.objects(codename=name, model=model_class).first()

        if permission:
            permission.principals.remove(self.id)
            permission.save()
            if hasattr(self, '_perm_cache'):
                delattr(self, '_perm_cache')

    def has_permission(self, name, cls_or_obj):
        # have not implemented object-level permissions yet
        if isinstance(self, User):
            if self.is_superuser and self.is_active:
                return True
            if not self.is_active:
                return False

        model_class = get_full_class_name(cls_or_obj)
        permissions = [p for p in self.permissions if p.model == model_class]

        return True if permissions else False

    @property
    def permissions(self):
        perm_cache = getattr(self, '_perm_cache', set())

        if not perm_cache:
            if isinstance(self, User):
                # if it's a User instance, first add group permissions,
                # this way, you can overwrite group-level permissions
                # with user-level permissions
                for group in self.groups:
                    perm_cache.update(group.permissions)
            # add own permissions
            perm_cache.update(Permission.objects(principals=self.id))

        self._perm_cache = perm_cache

        return self._perm_cache


class Group(Document, PrincipalMixin):
    pass


class User(Document, PrincipalMixin):
    is_active = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    groups = ListField(ReferenceField(Group))

    def set_password(self, plaintext):
        self.password = make_password(plaintext)


class AnonymousUser(object):
    id = None

    @property
    def is_active(self):
        return False

    @property
    def is_superuser(self):
        return False


class PrivilegeMixin(object):
    '''Mixin base class for creating subclasses that require
    class-level permissions.

    To use this mixin in a model class, add this to the list of base
    classes and if necessary, override the default permissions in the
    meta dictionary for that model class, for example:

    class MyModel(Document):
        myfield = StringField()

        meta = {
            # ...
            'permissions': (
                ('edit', 'Can edit'),
            ),
            # ...
        }
    '''
    default_permissions = (
        ('add', 'Can add'),
        ('change', 'Can change'),
        ('delete', 'Can delete'),
    )

    @classmethod
    def update_permissions(cls):
        class_perms = cls._meta.get('permissions', cls.default_permissions)
        model_class = get_full_class_name(cls)

        for class_perm in class_perms:
            permission = Permission.objects(
                model=model_class,
                codename=class_perm[0],
                name=class_perm[1]
            ).first()

            if not permission:
                Permission(
                    model=model_class,
                    codename=class_perm[0],
                    name=class_perm[1]
                ).save()


class Permission(Document):
    '''Basic model-level permissions'''
    codename = StringField(max_length=100)
    name = StringField(max_length=50)
    model = StringField()
    principals = ListField(ObjectIdField())
