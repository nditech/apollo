#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.conf import settings
from rapidsms.apps.base import AppBase
from models import *
import re
from datetime import datetime, timedelta
from django.utils.translation import ugettext as _


class App(AppBase):
    def __init__(self, router):
        '''form_prefixes = list(ChecklistForm.objects.all().values_list("prefix", flat=True))
        form_prefixes.extend(list(IncidentForm.objects.all().values_list("prefix", flat=True)))
        form_prefixes = list(set(form_prefixes)) # make the list unique

        prefix = settings.SMS_PREFIX if hasattr(settings, 'SMS_PREFIX') else ''
        pattern_string = prefix + r'(?P<observer_id>\d+)(?P<form_type>(' + "|".join(form_prefixes) + '))(?P<day>\d{1,2})(?P<location_type>(' + "|".join(LocationType.objects.all().exclude(in_form=False).values_list("code", flat=True)) + '))(?P<location_id>\d+)(!?)((?P<responses>[A-Z\d]{1,})@?((?P<comments>).*))?'
        self.pattern = re.compile(pattern_string, re.I)
        self.range_error_response = _('Invalid response(s) for question(s): "%s"')
        self.checklist_attribute_error_response = _('Invalid responses for the checklist code: "%s"')
        self.incident_attribute_error_response = _('Unknown critical incident code: "%s"')
        self.unknown_location = _('Unknown location with code: %s')
        self.unknown_observer = _('Observer ID not found. Please resend with valid Observer ID. You sent: %s')'''
        AppBase.__init__(self, router)

    def handle(self, message):
        # strip all unwanted whitespace and punctuation marks
        message.text = message.text.replace(";", " ").replace(",", " ").replace(":", " ").replace("/", " ").replace(".", " ")
        if not (message.text.find("@") == -1):
            text = message.text
            (part1, part2) = (text[0:text.find("@")], text[text.find("@"):])
            part1 = part1.upper().replace(" ", "").replace("O", "0").replace("I", "1").replace("L", "1").replace("&", "").replace("-", "").replace("?", "")
            message.text = part1 + part2
            message.message_only = part1
            message.comments_only = part2
        else:
            message.text = message.text.upper().replace(" ", "").replace("O", "0").replace("I", "1").replace("L", "1").replace("&", "").replace("-", "").replace("?", "")
            message.message_only = message.text

        if self.pattern.match(message.text):
            # Let's determine if we have a valid contact for this message
            match = self.pattern.match(message.text)
            try:
                message.observer = Contact.objects.get(observer_id=match.group('observer_id'))
            except Contact.DoesNotExist:
                return message.respond(self.unknown_observer % message.message_only)
            try:
                message.location = Location.objects.get(type__code=match.group('location_type'), code=match.group('location_id'))
            except Location.DoesNotExist:
                return message.respond(self.unknown_location % match.group('location_id'))

            # determine date of message
            # if the day is not specified, the date of the current day should be the value of key 'day'.
            if match.group('day'):
                day = int(match.group('day'))
            else:
                day = datetime.now().day

            # if the day being reported is greater than the current day,
            # then reference is being made of the previous month
            year = message.date.year
            month = message.date.month
            if day > message.date.day:
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
            # we don't want to lose the time portion of the date if this report is
            # meant for the current day
            if day != message.date.day:
                message.received_at = datetime(year, month, day)
            is_invalid_question = False
            is_invalid_response = False
            invalid_questions = []
            invalid_responses = []

            #To determine whether a message is a Checklist or an incident
            if (message.text.find("!") == -1):  # Then it is a checklist

                # Validating the checklist question types
                responses = self._parse_checklist(match.group('responses'))
                try:
                    checklist = Checklist.objects.get(location=message.location, observer=message.observer, date=message.received_at)
                    try:
                        checklist_form = ChecklistForm.objects.get(prefix=match.group('form_type'))
                        questions = ChecklistQuestion.objects.filter(form=checklist_form)
                        question_codes = questions.values_list('code', flat=True)
                        for question_code in responses.keys():
                            if question_code not in question_codes:
                                is_invalid_question = True
                                invalid_questions.append(question_code)
                            else:
                                question_regex = ChecklistQuestion.objects.get(form=checklist_form, code=question_code).type.validate_regex
                                if not re.compile(question_regex).match(responses[question_code]):
                                    is_invalid_response = True
                                    invalid_responses.append(question_code)
                                else:
                                    # the question code and response are valid now save or update
                                    if hasattr(message, 'comments_only'):
                                        checklist.comment = message.comments_only
                                    # update or add response to the checklist
                                    try:
                                        checklist_response = checklist.responses.get(question__code=question_code)
                                        checklist_response.response = responses[question_code]
                                        checklist_response.save()
                                    except ChecklistResponse.DoesNotExist:
                                        # the response doesn't exist, therefore create it
                                        checklist_response = ChecklistResponse.objects.create(checklist=checklist, \
                                            question=ChecklistQuestion.objects.get(form=checklist_form, code=question_code), \
                                            response=responses[question_code])
                                        checklist.responses.add(checklist_response)
                        if is_invalid_question:
                            return message.respond(self.checklist_attribute_error_response % ", ".join(invalid_questions))
                        elif is_invalid_response:
                            return message.respond(self.range_error_response % ", ".join(invalid_responses))
                        else:
                            # TODO: send a better success message
                            checklist_confirm = _("Correct Checklist")
                            return message.respond(checklist_confirm)
                    except ChecklistForm.DoesNotExist:
                        # checklist form type is invalid
                        return self.default(message)

                except Checklist.DoesNotExist:
                    # checklist doesn't exist
                    # TODO: send a more helpful error message
                    return self.default(message)

            else:
                #Validating the incident question responses
                responses = list(set(list(match.group('responses'))))
                incident_responses = []

                try:
                    incident_form = IncidentForm.objects.get(prefix=match.group('form_type'))
                    incident_response_codes = IncidentResponse.objects.filter(form=incident_form).values_list('code', flat=True)
                    for incident_response_code in responses:
                        if not incident_response_code in incident_response_codes:
                            is_invalid_response = True
                            invalid_responses.append(incident_response_code)
                        else:
                            # response code is valid
                            incident_responses.append(IncidentResponse.objects.get(form=incident_form, code=incident_response_code))

                    if is_invalid_response:
                        return message.respond(self.incident_attribute_error_response % ", ".join(invalid_responses))
                    else:
                        incident = Incident()
                        incident.location = message.location
                        incident.observer = message.observer
                        incident.date = message.received_at
                        incident.comment = message.comments_only if hasattr(message, "comments_only") else ""
                        incident.save()
                        for incident_response in incident_responses:
                            incident.responses.add(incident_response)

                        # TODO: use a better version of this response
                        incident_confirm = _("Correct Incident")
                        return message.respond(incident_confirm)

                except IncidentForm.DoesNotExist:
                    # incident form type is invalid
                    return self.default(message)

            # if all fails, send the default response
            return self.default(message)

    def default(self, message):
        default_message = _('Invalid message:"%s". Please resend!' % message.message_only)
        return message.respond(default_message)

    def _parse_checklist(self, responses):
        ''' Converts strings that look like A2C3D89AA90 into
            {'A':'2', 'C':'3', 'D':'89', 'AA':'90'}'''
        return dict(re.findall(r'([A-Z]{1,})([0-9]+)', responses.upper())) if responses else {}
