# -*- coding: utf-8 -*-
from flask import current_app
import requests

DATE_FORMAT_STRING = u'%m/%d/%Y'
HOUR_FORMAT_STRING = u'%H'
MINUTE_FORMAT_STRING = u'%M'
AM_PM_FORMAT_STRING = u'%p'


def report_incident(title, description, dt, category_id, coordinates,
                    location, firstname=None, lastname=None, email=None):
    server_url = current_app.config.get(u'USHAHIDI_SERVER')
    if not server_url:
        return

    incident_date = dt.strfmtime(DATE_FORMAT_STRING)
    incident_hour = dt.strfmtime(HOUR_FORMAT_STRING)
    incident_minute = dt.strfmtime(MINUTE_FORMAT_STRING)
    incident_ampm = dt.strfmtime(AM_PM_FORMAT_STRING).lower()

    payload = {
        'incident_title': title,
        'incident_description': description,
        'incident_date': incident_date,
        'incident_hour': incident_hour,
        'incident_minute': incident_minute,
        'incident_ampm': incident_ampm,
        'incident_category': category_id,
        'latitude': coordinates[0],
        'longitude': coordinates[1],
        'location_name': location
    }

    if firstname:
        payload['person_first'] = firstname

    if lastname:
        payload['person_last'] = lastname

    if email:
        payload['person_email'] = email

    requests.post(server_url, payload)
