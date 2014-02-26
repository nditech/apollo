from __future__ import unicode_literals
from mongoengine import Document, StringField
from altauth.documents import Group, Permission, ProtectedResourceMixin, User


class TreasureChest(Document, ProtectedResourceMixin):
    booty = StringField()

    meta = {
        'permissions': (
            ('loot', 'Can loot'),
            ('stash', 'Can stash'),
        )
    }


def test_error_without_update():
    user = User(
        username='user1',
        email='user@localdomain.us'
    ).save()

    try:
        user.add_permission('loot', TreasureChest)
    except Exception, e:
        assert isinstance(e, Permission.DoesNotExist)

    try:
        user.has_permission('loot', TreasureChest)
    except Exception, e:
        assert isinstance(e, Permission.DoesNotExist)

    try:
        user.remove_permission('loot', TreasureChest)
    except Exception, e:
        assert isinstance(e, Permission.DoesNotExist)

    user.delete()


def test_updated_permissions():
    TreasureChest.update_permissions()

    user = User(
        username='user1',
        email='user@localdomain.us'
    ).save()
    assert not user.has_permission('loot', TreasureChest)
    user.add_permission('loot', TreasureChest)
    assert user.has_permission('loot', TreasureChest)
    user.remove_permission('loot', TreasureChest)
    assert not user.has_permission('loot', TreasureChest)

    user.delete()


def test_propagated_permissions():
    TreasureChest.update_permissions()

    user = User(
        username='user1',
        email='user@localdomain.us'
    ).save()

    assert not user.has_permission('add', TreasureChest)

    user.delete()


def test_superuser_access():
    TreasureChest.update_permissions()

    user = User(
        username='user1',
        email='admin@localdomain.us',
        is_superuser=True
    ).save()

    user.has_permission('loot', TreasureChest)
    user.has_permission('add', TreasureChest)
    # even imaginary permissions
    user.has_permission('lobby', TreasureChest)
