# -*- coding: utf-8 -*-
from apollo import models, services


def get_participant_during_event(event, participant_id):
    current_event_ids = [i[0] for i in services.events.overlapping_events(
        event).with_entities(models.Event.id).all()]
    try:
        return services.participants.query.join(
            models.ParticipantSet,
            models.Participant.participant_set_id == models.ParticipantSet.id
        ).join(
            models.Event,
            models.Event.participant_set_id == models.ParticipantSet.id
        ).filter(
            models.Event.id.in_(current_event_ids),
            models.Participant.participant_id == participant_id
        ).one_or_none()
    except Exception:
        return None


def get_forms_for_event(event):
    current_event_ids = [i[0] for i in services.events.overlapping_events(
        event).with_entities(models.Event.id).all()]

    return services.forms.query.join(
        models.FormSet, models.Form.form_set_id == models.FormSet.id
    ).join(
        models.Event, models.Event.form_set_id == models.FormSet.id
    ).filter(
        models.Event.id.in_(current_event_ids)
    ).all()
