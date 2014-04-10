from flask.ext.principal import Permission, ActionNeed

view_events = Permission(ActionNeed('view_events'))
send_messages = Permission(ActionNeed('send_messages'))
add_submission = Permission(ActionNeed('add_submission'))
edit_submission = Permission(ActionNeed('edit_submission'))
export_submissions = Permission(ActionNeed('export_submissions'))
