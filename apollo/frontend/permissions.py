from flask import abort
from flask.ext.principal import Permission, ActionNeed, RoleNeed, ItemNeed

view_events = Permission(ActionNeed('view_events'), RoleNeed('admin'))
view_messages = Permission(ActionNeed('view_messages'), RoleNeed('admin'))
send_messages = Permission(ActionNeed('send_messages'), RoleNeed('admin'))
view_analyses = Permission(ActionNeed('view_analyses'), RoleNeed('admin'))
edit_participant = Permission(
    ActionNeed('edit_participant'), RoleNeed('admin'))
export_participants = Permission(
    ActionNeed('export_participants'), RoleNeed('admin'))
import_participants = Permission(
    ActionNeed('import_participants'), RoleNeed('admin'))
export_messages = Permission(
    ActionNeed('export_messages'), RoleNeed('admin'))

# submissions
add_submission = Permission(ActionNeed('add_submission'), RoleNeed('admin'))
edit_submission = Permission(
    ActionNeed('edit_submission'), RoleNeed('admin'))
export_submissions = Permission(
    ActionNeed('export_submissions'), RoleNeed('admin'))

# item permission
def require_item_perm(action, item, http_exception=403):
    perm = Permission(ItemNeed(action, item, 'object'), RoleNeed('admin'))
    if not perm.can():
        abort(http_exception, perm)
