# -*- coding: utf-8 -*-
def setup_permission_defaults(deployment)
    from apollo import services
    from apollo.frontend import permissions

    # install defaults
    for name in dir(permissions):
        item = getattr(permissions, name, None)
        if not isinstance(item, permissions.Permission):
            continue

        for need in item.needs:
            if need.method == 'action':
                services.perms.get_or_create(deployment=deployment,
                    action=need.value)


def setup_permission_fixtures(deployment)
    from apollo import models, services

    perm_role_fixtures = {
        'edit_both_submissions': ['analyst', 'manager'],
        'edit_forms': [],
        'import_participants': [],
        'send_messages': ['analyst', 'manager'],
        'add_submission': ['clerk', 'manager', 'analyst'],
        'edit_locations': [],
        'view_quality_assurance': ['analyst'],
        'edit_submission_quarantine_status': ['analyst'],
        'import_locations': [],
        'export_participants': [],
        'export_messages': [],
        'edit_submission_verification_status': ['analyst'],
        'view_messages': ['clerk', 'manager', 'analyst'],
        'view_events': ['clerk', 'analyst', 'manager'],
        'export_submissions': ['analyst', 'manager'],
        'view_result_analysis': ['analyst'],
        'edit_submission': ['clerk', 'manager', 'analyst'],
        'view_process_analysis': ['analyst'],
        'export_locations': [],
        'view_participants': ['manager', 'clerk', 'analyst'],
        'edit_participant': ['analyst', 'manager']
    }

    for perm_name, role_names in perm_role_fixtures.iteritems():
        perm = services.perms.get(deployment=deployment, action=perm_name)
        roles = list(models.Role.objects.filter(name__in=role_names))
        perm.update(add_to_set__entities=roles)
