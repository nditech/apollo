# -*- coding: utf-8 -*-
from http import HTTPStatus

from flask import g, jsonify, request
from flask_apispec import MethodResource, marshal_with, use_kwargs
from flask_babelex import gettext
from flask_jwt_extended import (
    create_access_token, create_refresh_token, get_jti,
    get_jwt_identity, get_raw_jwt, jwt_refresh_token_required,
    set_access_cookies, set_refresh_cookies, unset_access_cookies,
    unset_refresh_cookies)
from sqlalchemy import bindparam, func, or_, text, true
from sqlalchemy.orm.exc import NoResultFound
from webargs import fields

from apollo import settings
from apollo.api.common import BaseListResource
from apollo.api.decorators import protect
from apollo.core import csrf, red
from apollo.deployments.models import Event
from apollo.participants.api.schema import ParticipantSchema
from apollo.participants.models import (
    Participant, ParticipantSet, ParticipantFirstNameTranslations,
    ParticipantFullNameTranslations, ParticipantLastNameTranslations,
    ParticipantOtherNamesTranslations)


@marshal_with(ParticipantSchema)
@use_kwargs({'event_id': fields.Int()}, locations=['query'])
class ParticipantItemResource(MethodResource):
    @protect
    def get(self, participant_id, **kwargs):
        deployment = getattr(g, 'deployment', None)
        event = getattr(g, 'event', None)

        event_id = kwargs.get('event_id')
        if event_id:
            event = Event.query.filter_by(id=event_id).first_or_404()

        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        if event and event.participant_set_id:
            participant_set_id = event.participant_set_id
        else:
            participant_set_id = None

        participant = Participant.query.join(
            Participant.participant_set
        ).filter(
            ParticipantSet.id == participant_set_id,
            ParticipantSet.deployment_id == deployment_id,
            Participant.id == participant_id,
            Participant.participant_set_id == ParticipantSet.id
        ).first_or_404()

        return participant


@use_kwargs(
    {'event_id': fields.Int(), 'q': fields.String()}, locations=['query'])
class ParticipantListResource(BaseListResource):
    schema = ParticipantSchema()

    def get_items(self, **kwargs):
        event_id = kwargs.get('event_id')
        lookup_item = kwargs.get('q')

        deployment = getattr(g, 'deployment', None)
        if event_id is None:
            event = getattr(g, 'event', None)
        else:
            event = Event.query.filter_by(id=event_id).one()

        if deployment:
            deployment_id = deployment.id
        else:
            deployment_id = None

        if event and event.participant_set_id:
            participant_set_id = event.participant_set_id
        else:
            participant_set_id = None

        full_name_lat_query = ParticipantFullNameTranslations.lateral(
            'full_name')
        first_name_lat_query = ParticipantFirstNameTranslations.lateral(
            'first_name')
        other_names_lat_query = ParticipantOtherNamesTranslations.lateral(
            'other_names')
        last_name_lat_query = ParticipantLastNameTranslations.lateral(
            'last_name')

        queryset = Participant.query.select_from(
            Participant
        ).join(
            Participant.participant_set
        ).outerjoin(
            full_name_lat_query, true()
        ).outerjoin(
            first_name_lat_query, true()
        ).outerjoin(
            other_names_lat_query, true()
        ).outerjoin(
            last_name_lat_query, true()
        ).filter(
            Participant.participant_set_id == participant_set_id,
            ParticipantSet.deployment_id == deployment_id,
            ParticipantSet.id == participant_set_id)

        if lookup_item:
            queryset = queryset.filter(
                or_(
                    text('full_name.value ILIKE :name'),
                    func.btrim(
                        func.regexp_replace(
                            func.concat_ws(
                                ' ',
                                text('first_name.value'),
                                text('other_names.value'),
                                text('last_name.value'),
                            ), r'\s+', ' ', 'g'
                        )
                    ).ilike(f'%{lookup_item}%'),
                    Participant.participant_id.ilike(bindparam('pid'))
                )
            ).params(name=f'%{lookup_item}%', pid=f'{lookup_item}%')

        return queryset


@csrf.exempt
def login():
    request_data = request.json
    participant_id = request_data.get('participant_id')
    password = request_data.get('password')

    current_events = Event.overlapping_events(Event.default())
    participant = current_events.join(
        Participant,
        Participant.participant_set_id == Event.participant_set_id
    ).with_entities(
        Participant
    ).filter(
        Participant.participant_id == participant_id,
        Participant.password == password
    ).first()

    if participant is None:
        response = {'message': gettext('Login failed'), 'status': 'error'}
        return jsonify(response), HTTPStatus.FORBIDDEN

    access_token = create_access_token(
        identity=str(participant.uuid), fresh=True)
    refresh_token = create_refresh_token(identity=str(participant.uuid))

    access_jti = get_jti(encoded_token=access_token)
    refresh_jti = get_jti(encoded_token=refresh_token)

    red.set(access_jti, 'false', settings.JWT_ACCESS_TOKEN_EXPIRES * 1.1)
    red.set(refresh_jti, 'false', settings.JWT_REFRESH_TOKEN_EXPIRES * 1.1)

    # only return tokens if client explicitly requests it
    # and cookies are disabled
    send_jwts_in_response = 'cookies' not in settings.JWT_TOKEN_LOCATION or \
        (request.headers.get('X-TOKEN-IN-BODY') is not None)

    response = {
        'data': {
            'participant': {
                'events': [ev.id for ev in participant.participant_set.events],
                'first_name': participant.first_name,
                'other_names': participant.other_names,
                'last_name': participant.last_name,
                'full_name': participant.full_name,
                'participant_id': participant_id,
            },
        },
        'status': 'ok',
        'message': gettext('Login successful')
    }

    if send_jwts_in_response:
        response['data'].update(
            access_token=access_token, refresh_token=refresh_token)

        return jsonify(response)

    resp = jsonify(response)
    set_access_cookies(resp, access_token)
    set_refresh_cookies(resp, refresh_token)

    return resp


@csrf.exempt
@jwt_refresh_token_required
def refresh():
    participant_uuid = get_jwt_identity()
    try:
        participant = Participant.query.filter_by(uuid=participant_uuid).one()
    except NoResultFound:
        response = {
            'message': gettext('Invalid token supplied'),
            'status': 'error'
        }
        return jsonify(response), HTTPStatus.UNAUTHORIZED

    access_token = create_access_token(participant.uuid)

    # only return tokens if client explicitly requests it
    # and cookies are disabled
    send_jwts_in_response = 'cookies' not in settings.JWT_TOKEN_LOCATION or \
        (request.headers.get('X-TOKEN-IN-BODY') is not None)

    response = {
        'data': {},
        'status': 'ok'
    }

    if send_jwts_in_response:
        response['data'].update(access_token=access_token)

        return jsonify(response)

    resp = jsonify(response)
    set_access_cookies(resp, access_token)

    return resp


@csrf.exempt
@protect
def logout():
    jti = get_raw_jwt()['jti']
    red.set(jti, 'true', settings.JWT_ACCESS_TOKEN_EXPIRES * 1.1)

    response = {
        'status': 'ok',
        'message': gettext('Access token revoked')
    }
    resp = jsonify(response)
    unset_access_cookies(resp)

    return resp


@csrf.exempt
@jwt_refresh_token_required
def logout2():
    jti = get_raw_jwt()['jti']
    red.set(jti, 'true', settings.JWT_REFRESH_TOKEN_EXPIRES * 1.1)

    response = {
        'status': 'ok',
        'message': gettext('Refresh token revoked')
    }
    resp = jsonify(response)
    unset_refresh_cookies(resp)

    return resp
