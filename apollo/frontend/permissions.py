# -*- coding: utf-8 -*-
from flask import abort
from flask_principal import Permission, ActionNeed, RoleNeed, ItemNeed

# View
view_events = Permission(ActionNeed('view_events'), RoleNeed('admin'))
view_participants = Permission(
    ActionNeed('view_participants'), RoleNeed('admin'))
view_messages = Permission(ActionNeed('view_messages'), RoleNeed('admin'))
view_quality_assurance = Permission(
    ActionNeed('view_quality_assurance'), RoleNeed('admin'))
view_process_analysis = Permission(
    ActionNeed('view_process_analysis'), RoleNeed('admin'))
view_result_analysis = Permission(
    ActionNeed('view_result_analysis'), RoleNeed('admin'))

# Add
add_submission = Permission(ActionNeed('add_submission'), RoleNeed('admin'))

# Edit
edit_forms = Permission(ActionNeed('edit_forms'), RoleNeed('admin'))
edit_locations = Permission(ActionNeed('edit_locations'), RoleNeed('admin'))
edit_submission = Permission(ActionNeed('edit_submission'), RoleNeed('admin'))
edit_both_submissions = Permission(
    ActionNeed('edit_both_submissions'), RoleNeed('admin'))
edit_submission_quarantine_status = Permission(
    ActionNeed('edit_submission_quarantine_status'), RoleNeed('admin'))
edit_submission_verification_status = Permission(
    ActionNeed('edit_submission_verification_status'), RoleNeed('admin'))
edit_participant = Permission(
    ActionNeed('edit_participant'), RoleNeed('admin'))

# Import
import_participants = Permission(
    ActionNeed('import_participants'), RoleNeed('admin'))
import_locations = Permission(
    ActionNeed('import_locations'), RoleNeed('admin'))

# Export
export_participants = Permission(
    ActionNeed('export_participants'), RoleNeed('admin'))
export_messages = Permission(
    ActionNeed('export_messages'), RoleNeed('admin'))
export_submissions = Permission(
    ActionNeed('export_submissions'), RoleNeed('admin'))
export_locations = Permission(
    ActionNeed('export_locations'), RoleNeed('admin'))

# Others
send_messages = Permission(ActionNeed('send_messages'), RoleNeed('admin'))
delete_images = Permission(
    ActionNeed('delete_images'), RoleNeed('admin'))


def role(role):
    return Permission(RoleNeed(role))


# item permission
def require_item_perm(action, item, http_exception=403):
    perm = Permission(ItemNeed(action, item, 'object'), RoleNeed('admin'))
    if not perm.can():
        abort(http_exception, perm)


def can_access_resource(resource):
    perm = Permission(ItemNeed('access_resource', resource.resource_id,
                               resource.resource_type),
                      RoleNeed('admin'))
    return perm.can()
