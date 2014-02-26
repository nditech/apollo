from __future__ import unicode_literals
from django.contrib.auth.hashers import make_password
from mongoengine import BooleanField, Document, EmailField
from mongoengine import ListField, ObjectIdField, ReferenceField
from mongoengine import StringField
from .utils import get_full_class_name


class PrincipalMixin(object):
    '''Common mixin class for identities trying
    to access protected resources.
    '''
    def add_permission(self, name, cls):
        '''Adds a permission on a class to the current principal
        (a `User` or `Group` instance, in general). If the permission
        does not already exist, a DoesNotExist exception will be raised.'''

        # shortcut if this is a superuser
        if isinstance(self, User) and self.is_superuser:
            return

        model_class = get_full_class_name(cls)
        permission = Permission.objects.get(codename=name, model=model_class)

        principals = set(permission.principals)
        principals.add(self.id)
        permission.principals = list(principals)
        permission.save()

        self._invalidate_permissions_cache()

    def remove_permission(self, name, cls):
        '''Revokes a (previously granted) permission on a class
        from the current principal (a `User` or `Group` instance, usually).
        If the permission does not already exist, a DoesNotExist exception
        will be raised.'''

        # shortcut if this is a superuser
        if isinstance(self, User) and self.is_superuser:
            return

        model_class = get_full_class_name(cls)
        permission = Permission.objects.get(codename=name, model=model_class)

        principals = set(permission.principals)
        try:
            principals.remove(self.id)
        except KeyError:
            return

        permission.principals = list(principals)
        permission.save()

        self._invalidate_permissions_cache()


class ProtectedResourceMixin(object):
    '''A mixin class for adding permissions to a Document subclass.
    By default, three permissions are created per class; they cannot
    be overridden in the current implementation, but they can be supplemented.

    To add permissions to a Document, include `ProtectedResourceMixin` in the
    base class list, and optionally add any other permissions to the
    `meta` dictionary, for example:

    class TreasureChest(Document, ProtectedResourceMixin):
        booty = StringField()

        meta = {
            'permissions': (
                ('loot', 'Can loot'),
                ('store', 'Can store'),
            )
        }
    '''
    default_permissions = (
        ('add', 'Can add'),
        ('change', 'Can change'),
        ('delete', 'Can delete'),
    )

    @classmethod
    def update_permissions(cls):
        '''Creates any Permission documents for the current protected
        resource, if they do not exist. Necessary because Permission
        instances must exist before they are used. In general, this
        should be called from a management command.'''
        class_perms = dict(cls.default_permissions)
        class_perms.update(
            cls._meta.get('permissions', {})
        )
        model_class = get_full_class_name(cls)

        for codename, name in class_perms.iteritems():
            try:
                Permission.objects.get(
                    model=model_class,
                    codename=codename,
                    name=name
                )
            except Permission.DoesNotExist:
                Permission(
                    model=model_class,
                    codename=codename,
                    name=name
                ).save()


class Permission(Document):
    codename = StringField(max_length=50, unique_with='model')
    name = StringField(max_length=100)
    model = StringField()
    principals = ListField(ObjectIdField())


class ObjectPermission(Document):
    permission = ReferenceField(Permission)
    principals = ListField(ObjectIdField())


class Group(Document, PrincipalMixin):
    name = StringField()

    @property
    def permissions(self):
        perm_cache = getattr(self, '_perm_cache', set())

        if not perm_cache:
            perm_cache.update(Permission.objects(principal=self.id))
            self._perm_cache = perm_cache

        return self._perm_cache

    def _invalidate_permissions_cache(self):
        if hasattr(self, '_perm_cache'):
            delattr(self, '_perm_cache')

    def has_permission(self, name, cls):
        model_class = get_full_class_name(cls)
        permissions = [p for p in self.permissions if p.model == model_class]

        return True if permissions else False


class User(Document, PrincipalMixin):
    username = StringField(max_length=64)
    password = StringField(max_length=128)
    email = EmailField(max_length=128)
    is_active = BooleanField(default=True)
    is_superuser = BooleanField(default=False)
    groups = ListField(ReferenceField(Group))

    def _invalidate_permissions_cache(self):
        if hasattr(self, '_perm_cache'):
            delattr(self, '_perm_cache')
        if hasattr(self, '_group_perm_cache'):
            delattr(self, '_group_perm_cache')

    @property
    def user_permissions(self):
        perm_cache = getattr(self, '_perm_cache', set())

        if not perm_cache:
            perm_cache.update(Permission.objects(principals=self.id))
            self._perm_cache = perm_cache

        return self._perm_cache

    @property
    def group_permissions(self):
        group_perm_cache = getattr(self, '_group_perm_cache', set())

        if not group_perm_cache:
            for group in self.groups:
                group_perm_cache.update(Permission.objects(principals=group.id))

            self._group_perm_cache = group_perm_cache

        return self._group_perm_cache

    @property
    def all_permissions(self):

        permissions = set()
        permissions.update(self.group_permissions)
        permissions.update(self.user_permissions)

    def has_permission(self, name, cls):
        if self.is_superuser and self.is_active:
            return True

        if not self.is_active:
            return False

        model_class = get_full_class_name(cls)

        # check own permissions
        permissions = [p for p in self.user_permissions if p.model == model_class and p.codename == name]
        if permissions:
            return True

        # check group permissions
        group_permissions = [p for p in self.group_permissions if p.model == model_class and p.codename == name]
        if group_permissions:
            return True

        return False

    def is_anonymous(self):
        return False

    def set_password(self, plaintext):
        self.password = make_password(plaintext)
