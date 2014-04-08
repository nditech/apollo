from flask.ext.principal import Permission, ActionNeed

view_events = Permission(ActionNeed('view_events'))
send_messages = Permission(ActionNeed('send_messages'))
