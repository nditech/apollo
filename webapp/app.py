#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.apps.base import AppBase
from models import Location, Checklist, ChecklistForm, ChecklistQuestion, ChecklistQuestionOption, ChecklistQuestionType
from rapidsms.models import Contact
import re
from datetime import datetime, timedelta


class App(AppBase):
    def __init__(self, router):
        self.pattern = re.compile(r'PSC(?P<observer_id>\d+)(?P<form_type>(' + "|".join(ChecklistForm.objects.all().values_list("prefix", flat=True)) + '))(?P<day>\d{1,2})(?P<location_type>(' + "|".join(LocationType.objects.all().exclude(in_form=False).values_list("code", flat=True)) + '))(?P<location_id>\d+)(!?(?P<responses>[A-Z\d]{1,})@?((?P<comments>).*))?', re.I)
        self.range_error_response = 'Invalid response(s) for question(s): "%s"'
        self.checklist_attribute_error_response = 'Invalid responses for the checklist code: "%s"'
        self.incident_attribute_error_response = 'Unknown critical incident code: "%s"'
        
        AppBase.__init__(self, router)
        
    def handle(self, message):
        # strip all unwanted whitespace and punctuation marks
        message.text = message.text.replace(";", " ").replace(",", " ").replace(":", " ").replace("/", " ").replace(".", " ")
        if not (message.text.find("@") == -1):
            text = message.text
            (part1, part2) = (text[0:text.find("@")], text[text.find("@"):])
            part1 = part1.upper()
            part1 = part1.replace(" ", "").replace("O","0").replace("I","1").replace("L","1").replace("&","").replace("-","").replace("?","")
            message.text = part1 + part2
            message.message_only = part1
            message.comments_only = part2
            
        else:
            message.text = message.text.upper().replace(" ", "").replace("O","0").replace("I","1").replace("L","1").replace("&","").replace("-","").replace("?","")
            message.message_only = message.text

        if self.pattern.match(message.text):
            # Let's determine if we have a valid contact for this message
            match = self.pattern.match(message.text)
            try:
                message.observer = Contact.objects.get(observer_id=match.group('observer_id'))
            except Contact.DoesNotExist:
                return message.respond('Observer ID not found. Please resend with valid PSC. You sent: %s' % message.message_only)

            #if message.observer.phone[-10:] != message.connection.identity[-10:]:
            #    return message.respond('You are reporting from an unrecognised telephone number. Please call the NIC to update your phone number.')

            try:
                message.location = Location.objects.get(type__name=match.group('location_type'), code=match.group('location_id'))
            except Location.DoesNotExist:
                return message.respond('Unknown Location.')
                
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
            message.received_at = datetime(year, month, day)
                
            responses = self._parse_checklist(match.group('responses'))
            
            # Validating the question types
            
            checklist_form = ChecklistForm.objects.get(prefix=match.group('form_type'))
            questions = ChecklistQuestion.objects.filter(form=checklist_form)
            question_codes = questions.values_list('code', flat=True)
            for question_code in responses.keys():
                if question_code not in question_codes:
                    return message.respond('Invalid question')
            
            # Validating the question responses
            
            for question_code in responses.keys():
                question_regex = ChecklistQuestion.objects.get(form=checklist_form, code=question_code).type.validate_regex
                if not re.compile(question_regex).match(responses[question_code]):
                    return message.respond('Invalid response for question_code')
            
            return self.default(message)
    
    def default(self, message):
       return message.respond('Invalid message:"%s". Please resend!' % message.message_only)
    
    def _parse_checklist(self, responses):
        ''' Converts strings that look like A2C3D89AA90 into
            {'A':'2', 'C':'3', 'D':'89', 'AA':'90'}'''
        return dict(re.findall(r'([A-Z]{1,})([0-9]+)', responses.upper())) if responses else {}