# -*- coding: utf-8 -*-
from datetime import datetime

import re

from flask import g

from apollo import models, services
from apollo.core import db

ugly_phone = re.compile(r'[^\d]*')


def update_participant_completion_rating(participant):
    forms = services.forms.find(form_type='CHECKLIST')
    submissions = services.submissions.find(
        contributor=participant,
        form__in=forms,
        submission_type='O'
    )

    numerator = 0
    denominator = 0
    completion_map = {
        'Missing': 0,
        'Partial': 1,
        'Complete': 2,
        'Conflict': 2  # TODO: find a better way to compute the ratings
    }

    if submissions.count() == 0:
        participant.completion_rating = 1
    else:
        for submission in submissions:
            completion_values = [
                completion_map[i] for i in
                list(submission.completion.values())
            ]
            denominator += len(submission.form.groups) * 2.0
            numerator += sum(completion_values)

        try:
            participant.completion_rating = (numerator / denominator)
        except ZeroDivisionError:
            # this should never happen
            participant.completion_rating = 1
    participant.save()


def update_phone_contacts(participant, phone):
    phone_contact = next(filter(
        lambda contact: ugly_phone.sub('', phone) == contact.number,
        participant.phone_contacts), False)
    if phone_contact:
        phone_contact.last_seen = datetime.utcnow()
        participant.save()
    else:
        phone_contact = models.PhoneContact(
            number=phone, verified=False, last_seen=datetime.utcnow())
        participant.update(add_to_set__phones=phone_contact)

    return phone_contact.verified
