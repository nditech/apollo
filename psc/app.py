#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.apps.base import AppBase
from .models import Observer, RegistrationCenter, LGA, VRIncident, VRChecklist, DCOChecklist, DCOIncident, EDAYChecklist, EDAYIncident
from django.contrib.contenttypes.models import ContentType
import re
from datetime import datetime, timedelta
from decorators import role_required

class App(AppBase):
    def __init__(self, router):
        self.pattern = re.compile(r'PSC(?P<observer_id>\d{6})(DC|VR)?(\d{1,2})?(RC|GA)?(\d{3})?(!?([A-Z\d]{1,})@?(.*))?', re.I)
        self.vr_dc_pattern = re.compile(r'PSC(?P<observer_id>\d{6})(DC|VR)', re.I)
        self.vr_checklist  = re.compile(r'PSC(?P<observer_id>\d{6})VR(?P<day>\d{1,2})RC(?P<location_id>\d{3})(?P<responses>[A-Z\d]{2,})?@?(?P<comment>.*)', re.I)
        self.vr_incident  = re.compile(r'PSC(?P<observer_id>\d{6})VR(?P<day>\d{1,2})(?P<location_type>(RC|GA))(?P<location_id>\d{3})!(?P<responses>[A-Z]{1,})@?(?P<comment>.*)', re.I)
        self.dco_checklist = re.compile(r'PSC(?P<observer_id>\d{6})DC(?P<day>\d{1,2})RC(?P<location_id>\d{3})(?P<responses>[A-Z\d]{2,})?@?(?P<comment>.*)', re.I)
        self.dco_incident = re.compile(r'PSC(?P<observer_id>\d{6})DC(?P<day>\d{1,2})(?P<location_type>(RC|GA))(?P<location_id>\d{3})!(?P<responses>[A-Z]{1,})@?(?P<comment>.*)', re.I)
        self.eday_checklist = re.compile(r'PSC(?P<observer_id>\d{6})(?P<responses>[A-Z\d]{3,})?@?(?P<comment>.*)', re.I)
        self.eday_incident = re.compile(r'PSC(?P<observer_id>\d{6})!(?P<responses>[A-Z]{1,})@?(?P<comment>.*)', re.I)
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
                message.observer = Observer.objects.get(observer_id=match.group('observer_id'))
            except Observer.DoesNotExist:
                return message.respond('Observer ID not found. Please resend with valid PSC. You sent: %s' % message.message_only)

            #if message.observer.phone[-10:] != message.connection.identity[-10:]:
            #    return message.respond('You are reporting from an unrecognised telephone number. Please call the NIC to update your phone number.')

            # This is likely a valid PSC message
            if self.vr_dc_pattern.match(message.text):
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
            else:
                match = self.eday_incident.match(message.text)
                if match:
                    return self._eday_incident(message, match.groupdict())
                match = self.eday_checklist.match(message.text)
                if match:
                    return self._eday_checklist(message, match.groupdict())
            
            return self.default(message)
    
    def default(self, message):
       return message.respond('Invalid message:"%s". Please resend!' % message.message_only)

    @role_required('LGA')
    def _vr_checklist(self, msg, params):
        # determine location and date
        self._preprocess(msg, params)

        # Create the checklista
        try:
            vr = VRChecklist.objects.get(date=msg.date, observer=msg.observer)
            vr.location = msg.location
            vr.submitted = True
        except VRChecklist.DoesNotExist:
            vr = VRChecklist() 
            vr.date = msg.date
            vr.observer = msg.observer
            vr.location = msg.location
            vr.submitted = True

        if params['comment']:
            vr.comment = params['comment']

        responses = self._parse_checklist(params['responses'])

        for key in responses.keys():
            # validation
            if key == 'A' and int(responses[key]) in range(1, 5): # Time of opening of RC
                vr.A = int(responses[key])
            elif key in ['B', 'G', 'T', 'U', 'V', 'W', 'X'] and int(responses[key]) in range(1, 3):
                setattr(vr, key, int(responses[key]))
            elif key in ['C', 'F', 'Y', 'Z', 'AA']:
                if int(responses[key]) in (999,9999):
                    setattr(vr, key, 9999)
                else:
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
        vr.save()

        check = self._vrc_validate(responses)
        error_responses = []
        if check['attribute'] or check['range']:
            if check['attribute']:
                error_responses.append(self.checklist_attribute_error_response % (", ".join(check['attribute'])))
            if check['range']:
                error_responses.append(self.range_error_response % (", ".join(check['range'])))
            error_responses.append("You sent: %s" % msg.message_only)
            return msg.respond(". ".join(error_responses))
        else:
            return msg.respond('VR Checklist report accepted! You sent: %s' % msg.message_only)

    def _vr_incident(self, msg, params):
        # determine location and date
        self._preprocess(msg, params)

        # Create the Incident
        inc = VRIncident() 
        inc.date = msg.date
        inc.observer = msg.observer
        if msg.location:
            inc.location = msg.location

        for case in list(params['responses'].upper()):
            if hasattr(inc, case):
                setattr(inc, case, True)

        if params['comment']:
            inc.comment = params['comment']

        inc.save()

        check = self._vri_validate(params['responses'].upper())
        error_responses = []

        if check['attribute']:
            # generate error response
            if check['attribute']:
                error_responses.append(self.incident_attribute_error_response % (", ".join(check['attribute'])))
            error_responses.append("You sent: %s" % msg.message_only)
            return msg.respond(". ".join(error_responses))
        else:
            return msg.respond('VR Incident report accepted! You sent: %s' % msg.message_only)

    @role_required('LGA')
    def _dco_checklist(self, msg, params):
        # determine location and date
        self._preprocess(msg, params)

        # Create the checklist
        try:
            dco = DCOChecklist.objects.get(date=msg.date, observer=msg.observer)
            if msg.location:
                dco.location = msg.location
            dco.submitted =True
        except DCOChecklist.DoesNotExist:
            dco = DCOChecklist() 
            dco.date = msg.date
            dco.observer = msg.observer
            dco.location = msg.location
            dco.submitted = True
        except DCOChecklist.MultipleObjectsReturned:
            dco = DCOChecklist.objects.filter(date=msg.date, observer=msg.observer)[0]
            if msg.location:
                dco.location = msg.location
            dco.submitted =True


        if params['comment']:
            dco.comment = params['comment']

        responses = self._parse_checklist(params['responses'])

        for key in responses.keys():
            # validation
            if key in ['A', 'B', 'D', 'E', 'H', 'M', 'N', 'P', 'Q', 'R'] and int(responses[key]) in range(1, 3): # Yes or No
                setattr(dco, key, int(responses[key]))
            elif key in ['C', 'G']: # numeric responses
                if int(responses[key]) in (99,999,9999):
                    setattr(dco, key, 99)
                else:
                    setattr(dco, key, int(responses[key]))
            elif key in ['J', 'K', 'S', 'T', 'U', 'V', 'W', 'X']: # numeric responses
                if int(responses[key]) in (999,9999):
                    setattr(dco, key, 9999)
                else:
                    setattr(dco, key, int(responses[key]))
            elif key == 'F' and responses[key] == '9':
                setattr(dco, key+'9', True) 
            elif key == 'F' and not '9' in responses[key]:
                for opt in list(responses[key]):
                    if int(opt) in range(1, 9):
                        setattr(dco, key+opt, True)
        dco.save()

        check = self._dcoc_validate(responses)
        error_responses = []
        if check['attribute'] or check['range']:
            if check['attribute']:
                error_responses.append(self.checklist_attribute_error_response % (", ".join(check['attribute'])))
            if check['range']:
                error_responses.append(self.range_error_response % (", ".join(check['range'])))
            error_responses.append("You sent: %s" % msg.message_only)
            return msg.respond(". ".join(error_responses))
        else:
            return msg.respond('DCO Checklist report accepted! You sent: %s' % msg.message_only)

    def _dco_incident(self, msg, params):
        # determine location and date
        self._preprocess(msg, params)

        # Create the Incident
        inc = DCOIncident() 
        inc.date = msg.date
        inc.observer = msg.observer
        if msg.location:
           inc.location = msg.location

        for case in list(params['responses'].upper()):
            if hasattr(inc, case):
                setattr(inc, case, True)

        if params['comment']:
            inc.comment = params['comment']

        inc.save()

        check = self._dcoi_validate(params['responses'].upper())
        error_responses = []

        if check['attribute']:
            # generate error response
            if check['attribute']:
                error_responses.append(self.incident_attribute_error_response % (", ".join(check['attribute'])))
            error_responses.append("You sent: %s" % msg.message_only)
            return msg.respond(". ".join(error_responses))
        else:
            return msg.respond('DCO Incident report accepted! You sent: %s' % msg.message_only)
            
    def _eday_checklist(self, msg, params):
        # Create the checklist
        try:
            eday = EDAYChecklist.objects.filter(date__range=(msg.date-timedelta(3), msg.date), observer=msg.observer, checklist_index='1' if msg.observer.position == 1 else '2').order_by('-date')[0]
            eday.location = msg.observer.location
            eday.submitted = True
        except (EDAYChecklist.DoesNotExist, IndexError):
            eday = None

        responses = self._parse_checklist(params['responses'])

        if eday:
            for key in responses.keys():
                # validation
                if key == ['AA','BC','BF','BK','BN','CB','CF','CG','CH','CJ','CK','CM','CN','CP','CQ'] and int(responses[key]) in range(0, 4): #Yes/No questions
                    setattr(eday, key, int(responses[key]))
                elif key in ['BA','BG','BH','BJ','BM','CA','CC','CD','CE'] and int(responses[key]) in range(1, 6):
                    setattr(eday, key, int(responses[key]))
                elif key in ['DA', 'DB', 'DC', 'DD', 'DE', 'DF', 'DG', 'DH', 'EA', 'EB', 'EC', 'ED', 'EE', 'EF', 'EG', 'EH', 'EJ', 'EK', 'EM', 'EN', 'EP', 'EQ', 'ER', 'ES', 'ET', 'EU', 'EV', 'EW', 'EX', 'EY', 'EZ', 'FA', 'FB', 'FC', 'FD', 'FE', 'FF', 'FG'] and int(responses[key]) <= 5000:
                    setattr(eday, key, int(responses[key]))
                elif key in ['BD'] and int(responses[key]) <= 9:
                    eday.BD == int(responses[key])
                elif key in ['BE'] and int(responses[key]) <= 99:
                    eday.BE == int(responses[key])
                elif key in ['BB'] and int(responses[key]) <= 999:
                    eday.BB == int(responses[key])
                elif key in ['BP'] and int(responses[key]) <= 3500:
                    eday.BP == int(responses[key])
                
            if params['comment']:
                eday.comment = params['comment']
            
            eday.save()

        check = self._edayc_validate(responses)
        
        error_responses = []
        if check['attribute'] or check['range']:
            if check['attribute']:
                error_responses.append(self.checklist_attribute_error_response % (", ".join(check['attribute'])))
            if check['range']:
                error_responses.append(self.range_error_response % (", ".join(check['range'])))
            error_responses.append("You sent: %s" % msg.message_only)
            return msg.respond(". ".join(error_responses))
        else:
            return msg.respond('EDAY Checklist report accepted! You sent: %s' % msg.message_only)

    def _eday_incident(self, msg, params):
        # Create the Incident
        inc = EDAYIncident() 
        inc.date = msg.date
        inc.observer = msg.observer
        if msg.observer.location:
            inc.location = msg.observer.location

        for case in list(params['responses'].upper()):
            if hasattr(inc, case):
                setattr(inc, case, True)

        if params['comment']:
            inc.comment = params['comment']

        inc.save()

        check = self._edayi_validate(params['responses'].upper())
        error_responses = []

        if check['attribute']:
            # generate error response
            if check['attribute']:
                error_responses.append(self.incident_attribute_error_response % (", ".join(check['attribute'])))
            error_responses.append("You sent: %s" % msg.message_only)
            return msg.respond(". ".join(error_responses))
        else:
            return msg.respond('EDAY Incident report accepted! You sent: %s' % msg.message_only)
    
    def _parse_checklist(self, responses):
        ''' Converts strings that look like A2C3D89AA90 into
            {'A':'2', 'C':'3', 'D':'89', 'AA':'90'}'''
        return dict(re.findall(r'([A-Z]{1,})([0-9]+)', responses.upper())) if responses else {}

    def _vrc_validate(self, responses):
        range_error = []
        attribute_error = []
        for key in responses.keys():
            if key not in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'AA']: attribute_error.append(key)
            if key in ['A'] and int(responses[key]) not in range(1,5): range_error.append(key)
            elif key in ['B', 'G', 'T', 'U', 'V', 'W', 'X'] and int(responses[key]) not in range(1, 3): range_error.append(key)
            elif key in ['H', 'J', 'K', 'M', 'N', 'P', 'Q','R','S'] and int(responses[key]) not in range(1, 6): range_error.append(key)
            elif key in ['C'] and int(responses[key]) > 10: range_error.append(key)
            elif key in ['F'] and int(responses[key]) > 60: range_error.append(key)
            if key in ['Y', 'Z', 'AA'] and int(responses[key]) > 9999: range_error.append(key)
            if key in ['Y','Z','AA'] and int(responses[key]) == 999:
                responses[key] = 9999
            elif key in ['D']:
                r = filter(lambda x: True if x not in ['1','2','3','4'] else False, responses['D'])
                if r:
                    range_error.append(key)
                elif '4' in responses['D'] and len(responses['D'].replace('4','')) > 0: range_error.append(key)
            elif key in ['E']:
                s = filter(lambda y: True if y not in ['1','2','3','4','5'] else False, responses['E'])
                if s: range_error.append(key)
                elif '5' in responses['E'] and len(responses['E'].replace('5','')) > 0: range_error.append(key)
        return {'range': range_error, 'attribute': attribute_error }
        
    def _vri_validate(self, message):
        attribute_error = []
        for key in list(message):
            if key not in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'M', 'N', 'P', 'Q']: attribute_error.append(key)
        return {'attribute': attribute_error }
        
    def _dcoc_validate(self, responses):
        range_error = []
        attribute_error = []
        for key in responses.keys():
            if key not in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']: attribute_error.append(key)
            if key in ['A', 'B', 'D', 'E', 'H', 'M', 'N','P', 'Q','R'] and int(responses[key]) not in range(1, 3): range_error.append(key)
            elif key in ['C'] and int(responses[key]) > 10: range_error.append(key)
            elif key in ['G'] and int(responses[key]) > 60: range_error.append(key)
            if key in ['J', 'K','S', 'T', 'U', 'V', 'W', 'X'] and int(responses[key]) > 9999: range_error.append(key)
            if key in ['J', 'K','S', 'T', 'U', 'V', 'W', 'X'] and int(responses[key]) == 999:
                responses[key] = 9999
            elif key in ['F']:
                r = filter(lambda x: True if x not in ['1','2','3','4','5','6','7','8','9'] else False, responses['D'])
                if r: range_error.append(key)
                elif '9' in responses['F'] and len(responses['F'].replace('9','')) > 0: range_error.append(key)
        return {'range': range_error, 'attribute': attribute_error }
        
        
    def _dcoi_validate(self, message):
        attribute_error = []
        for key in list(message):
            if key not in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K']: attribute_error.append(key)
        return {'attribute': attribute_error }
        
    def _edayc_validate(self, responses):
        range_error = []
        attribute_error = []
        for key in responses.keys():
            if key not in ['AA', 'BA', 'BB', 'BC', 'BD', 'BE', 'BF', 'BG', 'BH', 'BJ', 'BK', 'BM', 'BN', 'BP', 'CA', 'CB', 'CC', 'CD', 'CE', 'CF', 'CG', 'CH', 'CJ', 'CK', 'CM', 'CN', 'CP', 'CQ', 'DA', 'DB', 'DC', 'DD', 'DE', 'DF', 'DG', 'DH', 'EA', 'EB', 'EC', 'ED', 'EE', 'EF', 'EG', 'EH', 'EJ', 'EK', 'EM', 'EN', 'EP', 'EQ', 'ER', 'ES', 'ET', 'EU', 'EV', 'EW', 'EX', 'EY', 'EZ', 'FA', 'FB', 'FC', 'FD', 'FE', 'FF', 'FG']: attribute_error.append(key)
            if key in ['AA','BC','BF','BK','BN','CB','CF','CG','CH','CJ','CK','CM','CN','CP','CQ'] and int(responses[key]) not in range(0,4): range_error.append(key)
            elif key in ['BA','BG','BH','BJ','BM','CA','CC','CD','CE'] and int(responses[key]) not in range(1, 6): range_error.append(key)
            elif key in ['DA', 'DB', 'DC', 'DD', 'DE', 'DF', 'DG', 'DH'] and int(responses[key]) > 5000: range_error.append(key)
            elif key in ['EA', 'EB', 'EC', 'ED', 'EE', 'EF', 'EG', 'EH', 'EJ', 'EK', 'EM', 'EN', 'EP', 'EQ', 'ER', 'ES', 'ET', 'EU', 'EV', 'EW', 'EX', 'EY', 'EZ', 'FA', 'FB', 'FC', 'FD', 'FE', 'FF', 'FG'] and int(responses[key]) > 5000: range_error.append(key)
            elif key in ['BD'] and int(responses[key]) > 9: range_error.append(key)
            elif key in ['BE'] and int(responses[key]) > 99: range_error.append(key)
            elif key in ['BB'] and int(responses[key]) > 999: range_error.append(key)
            elif key in ['BP'] and int(responses[key]) > 3500: range_error.append(key)
        return {'range': range_error, 'attribute': attribute_error }
        
    def _edayi_validate(self, message):
        attribute_error = []
        for key in list(message):
            if key not in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T']: attribute_error.append(key)
        return {'attribute': attribute_error }

    def _preprocess(self, message, params):
        # determine location
        if params.has_key('location_type') and params['location_type'].upper() == 'GA':
            try:
                location = LGA.objects.get(code=params['location_id'])
                location = RegistrationCenter.objects.get(parent=location,code='999')
            except LGA.DoesNotExist:
                lga = LGA.objects.get(name="Unknown")
                location = RegistrationCenter.objects.get(parent=lga,code="999")
            except RegistrationCenter.DoesNotExist:
                lga = LGA.objects.get(name="Unknown")
                location = RegistrationCenter.objects.get(parent=lga,code="999")
        else:
            try:
                if message.observer.location_type == ContentType.objects.get_for_model(LGA.objects.get(pk=1)):
                    lga = LGA.objects.get(pk=message.observer.location_id)
                    location = RegistrationCenter.objects.get(parent=lga,code=params['location_id'])
                else:
                    lga = LGA.objects.get(name="Unknown")
                    location = RegistrationCenter.objects.get(parent=lga,code="999")
            except RegistrationCenter.DoesNotExist:
                lga = LGA.objects.get(name="Unknown")
                location = RegistrationCenter.objects.get(parent=lga,code="999")

        message.location = location

        # determine date of message
        # if the day is not specified, the date of the current day should be the value of key 'day'.
        if params.has_key('day'):
            day = int(params['day'])
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
