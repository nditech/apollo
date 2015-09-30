from apollo.core import Service
from apollo.users.models import User, Need, UserUpload
from flask import g
from flask.ext.principal import ActionNeed, ItemNeed


class UsersService(Service):
    __model__ = User


class UserUploadsService(Service):
    __model__ = UserUpload

    def _set_default_filter_parameters(self, kwargs):
        # need to override adding the deployment, because
        # it's already connected to the user
        return kwargs


class PermsService(Service):
    __model__ = Need

    def _get_needs_for_user(self, user):
        needs = []
        needs_for_user = self.__model__.objects.filter(
            entities=user, deployment=user.deployment)
        for need in needs_for_user:
            if need.items:
                items = filter(lambda i: type(i) != dict, list(need.items))
                needs.extend([ItemNeed(need.action, item, 'object')
                             for item in items])
            else:
                needs.append(ActionNeed(need.action))
        return needs

    def _get_needs_for_roles(self, user):
        needs = []
        needs_for_roles = self.__model__.objects.filter(
            entities__in=user.roles, deployment=user.deployment)
        for need in needs_for_roles:
            if need.items:
                items = filter(lambda i: type(i) != dict, list(need.items))
                needs.extend([ItemNeed(need.action, item, 'object')
                             for item in items])
            else:
                needs.append(ActionNeed(need.action))
        return needs

    def get_all_needs(self, user):
        user_needs = self._get_needs_for_user(user)
        roles_needs = self._get_needs_for_roles(user)
        return set(user_needs + roles_needs)

    def add_action_need_to_entity(self, entity, action):
        try:
            need = self.__model__.objects.get(
                action=action, deployment=g.deployment)
            if entity in need.entities:
                return need
            need.update(add_to_set__entities=entity)
        except self.__model__.DoesNotExist:
            need = self.__model__(
                action=action, entities=[entity], deployment=g.deployment)
            need.save()

        return need

    def remove_action_need_from_entity(self, entity, action):
        try:
            need = self.__model__.objects.get(
                action=action, deployment=g.deployment)
            if entity in need.entities:
                need.entities.remove(entity)
                need.save()
        except self.__model__.DoesNotExist:
            pass

    def add_item_need_to_entity(self, entity, action, item):
        try:
            need = self.__model__.objects.get(
                action=action, deployment=g.deployment)
            if entity in need.entities and item in need.items:
                return need
            if not entity in need.entities:
                need.update(add_to_set__entities=entity)
            if not item in need.items:
                need.update(add_to_set__items=item)
        except self.__model__.DoesNotExist:
            need = self.__model__(
                action=action, entities=[entity], items=[item],
                deployment=g.deployment)
            need.save()

        return need

    def remove_item_need_from_entity(self, entity, action, item):
        try:
            need = self.__model__.objects.get(
                action=action, deployment=g.deployment)
            if entity in need.entities and item in need.items:
                need.items.remove(item)
                need.save()
        except self.__model__.DoesNotExist:
            pass
