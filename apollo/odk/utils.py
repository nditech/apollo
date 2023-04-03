# -*- coding: utf-8 -*-
import base64
import io
import json
import zlib
from urllib.parse import urljoin

import qrcode
from PIL import Image
from flask import url_for

from apollo.settings import SSL_REQUIRED


def make_message_text(form, participant, data, serial: str = None) -> str:
    message_body = f'{form.prefix} {participant.participant_id}'

    if form.form_type == 'INCIDENT':
        message_body += '!'
    if serial and form.form_type == 'SURVEY':
        message_body += f'X{serial}'

    for tag in form.tags:
        field_value = data.get(tag)
        if field_value is None:
            continue

        field = form.get_field_by_tag(tag)
        if field.get('type') == 'multiselect':
            value_rep = ''.join(str(i) for i in sorted(field_value))
        elif field.get('type') == 'image':
            continue
        else:
            value_rep = field_value

        message_body += f' {tag}{value_rep}'

    return message_body


def generate_config_qr_code(participant=None):
    scheme = 'https' if SSL_REQUIRED else 'http'
    settings = {
        'general': {
            'server_url': urljoin(
                url_for('dashboard.index', _external=True, _scheme=scheme),
                'xforms'
            )
        },
        'admin': {}
    }

    if participant is not None:
        settings['general'].update(
            username=participant.participant_id,
            password=participant.password
        )

    json_bytes = json.dumps(settings).encode('UTF-8')
    compressed_json = zlib.compress(json_bytes)

    qr_code = qrcode.QRCode(
        version=1, error_correction=qrcode.ERROR_CORRECT_L, box_size=10,
        border=4
    )
    qr_code.add_data(base64.b64encode(compressed_json))
    qr_code.make()

    img_buffer = io.BytesIO()
    img = qr_code.make_image(fill_color='black', back_color='white')

    thumb_size = (256, 256)
    img.thumbnail(thumb_size, Image.ANTIALIAS)

    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)

    return img_buffer.getvalue()
