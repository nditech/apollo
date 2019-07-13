# -*- coding: utf-8 -*-
def make_message_text(form, participant, data):
    message_body = f'{form.prefix} {participant.participant_id}'

    for tag in form.tags:
        field_value = data.get(tag)
        if field_value is None:
            continue

        field = form.get_field_by_tag(tag)
        if field.get('type') == 'multiselect':
            value_rep = ''.join(sorted(field_value))
        else:
            value_rep = field_value

        message_body += f' {tag}{value_rep}'

    return message_body
