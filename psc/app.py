#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.apps.base import AppBase
from .models import Observer, RegistrationCenter, LGA, VRIncident, VRChecklist, DCOChecklist, DCOIncident
from django.contrib.contenttypes.models import ContentType
import re
from datetime import datetime

class App(AppBase):
    def __init__(self, router):
        self.pattern = re.compile(r'PSC(?P<observer_id>\d{6})(DC|VR)(\d{2})(RC|GA)(\d{3})(!?([A-Z\d]{1,})@?(.*))?', re.I)
        self.vr_checklist  = re.compile(r'PSC(?P<observer_id>\d{6})VR(?P<day>\d{2})RC(?P<location_id>\d{3})(?P<responses>[ABCDEFGHJKMNPQRSTUVWXYZ\d]{2,})?', re.I)
        self.vr_incident  = re.compile(r'PSC(?P<observer_id>\d{6})VR(?P<day>\d{2})(?P<location_type>(RC|GA))(?P<location_id>\d{3})!(?P<responses>[ABCDEFGHJKMNPQ]{1,})@?(?P<comment>.*)', re.I)
        self.dco_checklist = re.compile(r'PSC(?P<observer_id>\d{6})DC(?P<day>\d{2})RC(?P<location_id>\d{3})(?P<responses>[ABCDEFGHJKMNPQRSTUVWX\d]{2,})?', re.I)
        self.dco_incident = re.compile(r'PSC(?P<observer_id>\d{6})DC(?P<day>\d{2})(?P<location_type>(RC|GA))(?P<location_id>\d{3})!(?P<responses>[ABCDEFGHJK]{1,})@?(?P<comment>.*)', re.I)
        AppBase.__init__(self, router)
        
    def handle(self, message):
        # strip all unwanted whitespace and punctuation marks
        message.text = message.text.replace(" ", "").replace(";", "").replace(",", "").replace(":", "").replace("/", "").replace(".", "")
        if self.pattern.match(message.text):
            # Let's determine if we have a valid contact for this message
            match = self.pattern.match(message.text)
            try:
                message.observer = Observer.objects.get(observer_id=match.group('observer_id'))
            except Observer.DoesNotExist:
                return message.respond('You are not authorized to send reports to this number.')

            # This is likely a valid PSC message
            match = self.vr_incident.match(message.text)
            if match:
                return self._vr_incident(message, match.groupdict())
            match = self.vr_checklist.match(message.text)
            if match:
                return self._vr_checklist(message, match.groupdict())
            match = self.dco_incident.match(message.text)
            if match:
                return self._dco_incident(message, match.groupdict())
            match = self.dco_checklist.match(message.text)
            if match:
                return self._dco_checklist(message, match.groupdict())
            
            return self.default(message)
    
    def default(self, message):
       return message.respond('Invalid message: %s' % message.text)

    def _vr_checklist(self, msg, params):
        # determine location
        try:
            location = RegistrationCenter.objects.get(code=params['location_id'])
        except RegistrationCenter.DoesNotExist:
            if int(params['location_id']) == 999:
                location = None
            else:
                return self.default(msg)

        # determine date of message
        day = int(params['day'])

        # if the day being reported is greater than the current day,
        # then reference is being made of the previous month
        year = msg.date.year
        month = msg.date.month
        if day > msg.date.day:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        msg.received_at = datetime(year, month, day)

        # Create the checklist
        try:
            if location:
                vr = VRChecklist.objects.get(date=msg.date, observer=msg.observer, 
                    location_type=ContentType.objects.get_for_model(location), location_id=location.pk)
            else:
                vr = VRChecklist.objects.get(date=msg.date, observer=msg.observer)
        except VRChecklist.DoesNotExist:
            vr = VRChecklist() 
            vr.date = msg.date
            vr.observer = msg.observer
            vr.location = location

        responses = self._parse_checklist(params['responses'])

        for key in responses.keys():
            # validation
            if key == 'A' and int(responses[key]) in range(1, 5): # Time of opening of RC
                vr.A = int(responses[key])
            elif key in ['B', 'G', 'T', 'U', 'V', 'W', 'X'] and int(responses[key]) in range(1, 3):
                setattr(vr, key, True if int(responses[key]) == 1 else False)
            elif key in ['C', 'F', 'Y', 'Z', 'AA']:
                setattr(vr, key, int(responses[key]))
            elif key in ['H', 'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S'] and int(responses[key]) in range(1, 6):
                setattr(vr, key, int(responses[key]))
            elif key == 'D' and responses[key] == '4':
                setattr(vr, key+'4', True) 
            elif key == 'D' and not '4' in responses[key]:
                for opt in list(responses[key]):
                    if int(opt) in range(1, 4):
                        setattr(vr, key+opt, True)
            elif key == 'E' and responses[key] == '5':
                setattr(vr, key+'5', True) 
            elif key == 'E' and not '5' in responses[key]:
                for opt in list(responses[key]):
                    if int(opt) in range(1, 5):
                        setattr(vr, key+opt, True)
            else:
                return self.default(msg)
        vr.save()
        return msg.respond('Checklist report accepted! You sent: %s' % msg.text)

    def _vr_incident(self, msg, params):
        # determine location
        if params['location_type'].upper() == 'RC':
            try:
                location = RegistrationCenter.objects.get(code=params['location_id'])
            except RegistrationCenter.DoesNotExist:
                if int(params['location_id']) == 999:
                    location = None
                else:
                    return self.default(msg)
        else:
            try:
                location = LGA.objects.get(code=params['location_id'])
            except LGA.DoesNotExist:
                if int(params['location_id']) == 999:
                    location = None
                else:
                    return self.default(msg)

        # determine date of message
        day = int(params['day'])

        # if the day being reported is greater than the current day,
        # then reference is being made of the previous month
        year = msg.date.year
        month = msg.date.month
        if day > msg.date.day:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        msg.received_at = datetime(year, month, day)

        # Create the Incident
        inc = VRIncident() 
        inc.date = msg.date
        inc.observer = msg.observer
        if location:
            inc.location = location

        for case in list(params['responses'].upper()):
            if hasattr(inc, case):
                setattr(inc, case, True)

        if params['comment']:
            inc.comment = params['comment']

        inc.save()

        return msg.respond('Incident report accepted! You sent: %s' % msg.text)

    def _dco_checklist(self, msg, params):
        # determine location
        try:
            location = RegistrationCenter.objects.get(code=params['location_id'])
        except RegistrationCenter.DoesNotExist:
            if int(params['location_id']) == 999:
                location = None
            else:
                return self.default(msg)

        # determine date of message
        day = int(params['day'])

        # if the day being reported is greater than the current day,
        # then reference is being made of the previous month
        year = msg.date.year
        month = msg.date.month
        if day > msg.date.day:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        msg.received_at = datetime(year, month, day)

        # Create the checklist
        try:
            if location:
                dco = DCOChecklist.objects.get(date=msg.date, observer=msg.observer, 
                        location_type=ContentType.objects.get_for_model(location), location_id=location.pk)
            else:
                dco = DCOChecklist.objects.get(date=msg.date, observer=msg.observer)
        except DCOChecklist.DoesNotExist:
            dco = DCOChecklist() 
            dco.date = msg.date
            dco.observer = msg.observer
            dco.location = location

        responses = self._parse_checklist(params['responses'])

        for key in responses.keys():
            # validation
            if key in ['A', 'B', 'D', 'E', 'H', 'M', 'N', 'P', 'Q', 'R'] and int(responses[key]) in range(1, 3): # Yes or No
                setattr(dco, key, True if int(responses[key]) == 1 else False)
            elif key in ['C', 'G', 'J', 'K', 'S', 'T', 'U', 'V', 'W', 'X']: # numeric responses
                setattr(dco, key, int(responses[key]))
            elif key == 'F' and responses[key] == '9':
                setattr(dco, key+'9', True) 
            elif key == 'F' and not '9' in responses[key]:
                for opt in list(responses[key]):
                    if int(opt) in range(1, 9):
                        setattr(dco, key+opt, True)
            else:
                return self.default(msg)
        dco.save()
        return msg.respond('Checklist report accepted! You sent: %s' % msg.text)

    def _dco_incident(self, msg, params):
        # determine location
        if params['location_type'].upper() == 'RC':
            try:
                location = RegistrationCenter.objects.get(code=params['location_id'])
            except RegistrationCenter.DoesNotExist:
                if int(params['location_id']) == 999:
                    location = None
                else:
                    return self.default(msg)
        else:
            try:
                location = LGA.objects.get(code=params['location_id'])
            except LGA.DoesNotExist:
                if int(params['location_id']) == 999:
                    location = None
                else:
                    return self.default(msg)

        # determine date of message
        day = int(params['day'])

        # if the day being reported is greater than the current day,
        # then reference is being made of the previous month
        year = msg.date.year
        month = msg.date.month
        if day > msg.date.day:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
        msg.received_at = datetime(year, month, day)

        # Create the Incident
        inc = DCOIncident() 
        inc.date = msg.date
        inc.observer = msg.observer
        if location:
           inc.location = location

        for case in list(params['responses'].upper()):
            if hasattr(inc, case):
                setattr(inc, case, True)

        if params['comment']:
            inc.comment = params['comment']

        inc.save()

        return msg.respond('Incident report accepted! You sent: %s' % msg.text)

    def _parse_checklist(self, responses):
        ''' Converts strings that look like A2C3D89AA90 into
            {'A':'2', 'C':'3', 'D':'89', 'AA':'90'}'''
        return dict(re.findall(r'([A-Z]{1,2})([0-9]+)', responses.upper())) if responses else {}

