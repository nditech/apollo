from flask import g
from flask.ext.script import Command, prompt_choices
from flask.ext.principal import Permission
from apollo.frontend import permissions
from apollo import models, services


class AddPermissionToRole(Command):
    '''Adds a specified permission to a role'''

    def run(self):
        deployments = models.Deployment.objects.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        g.deployment = deployments[int(option) - 1]

        roles = models.Role.objects.all()
        option = prompt_choices('Role', [
            (str(i), v) for i, v in enumerate(roles, 1)])
        role = roles[int(option) - 1]
        all_permissions = filter(
            lambda key: isinstance(getattr(permissions, key), Permission),
            sorted(permissions.__dict__.keys()))

        all_needs = set()
        for perm in all_permissions:
            all_needs.update(getattr(permissions, perm).needs)

        presentable_needs = sorted(map(lambda need: need.value, filter(
            lambda need: need.method == 'action', all_needs)))

        option = prompt_choices('Permission', [
            (str(i), v) for i, v in enumerate(presentable_needs, 1)])
        need = presentable_needs[int(option) - 1]

        services.perms.add_action_need_to_entity(role, need)


class ListPermissionsOfRole(Command):
    '''List permission for a role'''

    def run(self):
        deployments = models.Deployment.objects.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        g.deployment = deployments[int(option) - 1]

        roles = models.Role.objects.all()
        option = prompt_choices('Role', [
            (str(i), v) for i, v in enumerate(roles, 1)])
        role = roles[int(option) - 1]

        for need in models.Need.objects.filter(
            entities=role, deployment=g.deployment
        ):
            print need.action


class RemovePermissionFromRole(Command):
    '''Remove a permission from a role'''

    def run(self):
        deployments = models.Deployment.objects.all()
        option = prompt_choices('Deployment', [
            (str(i), v) for i, v in enumerate(deployments, 1)])
        g.deployment = deployments[int(option) - 1]

        roles = models.Role.objects.all()
        option = prompt_choices('Role', [
            (str(i), v) for i, v in enumerate(roles, 1)])
        role = roles[int(option) - 1]
        all_permissions = filter(
            lambda key: isinstance(getattr(permissions, key), Permission),
            sorted(permissions.__dict__.keys()))

        all_needs = set()
        for perm in all_permissions:
            all_needs.update(getattr(permissions, perm).needs)

        presentable_needs = sorted(map(lambda need: need.value, filter(
            lambda need: need.method == 'action', all_needs)))

        option = prompt_choices('Permission', [
            (str(i), v) for i, v in enumerate(presentable_needs, 1)])
        need = presentable_needs[int(option) - 1]

        services.perms.remove_action_need_from_entity(role, need)
