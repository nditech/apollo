from flask.ext.principal import Permission, ActionNeed, RoleNeed

view_events = Permission(ActionNeed('view_events'), RoleNeed('admin'))
send_messages = Permission(ActionNeed('send_messages'), RoleNeed('admin'))
edit_participant = Permission(
    ActionNeed('edit_participant'), RoleNeed('admin'))
export_participants = Permission(
    ActionNeed('export_participants'), RoleNeed('admin'))

# submissions
add_submission = Permission(ActionNeed('add_submission'), RoleNeed('admin'))
edit_submission = Permission(
    ActionNeed('edit_submission'), RoleNeed('admin'))
export_submissions = Permission(
    ActionNeed('export_submissions'), RoleNeed('admin'))
