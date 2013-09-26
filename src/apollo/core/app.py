#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import string
from django.conf import settings
from rapidsms.apps.base import AppBase
import reversion
from models import *
from datetime import datetime
from django.utils import translation
from django.utils.translation import ugettext as _
from django.contrib.sites.models import Site
from django.contrib.comments.models import Comment

PUNCTUATIONS = filter(lambda s: s not in settings.ALLOWED_PUNCTUATIONS, string.punctuation) + ' '
TRANS_TABLE = dict((ord(fro), ord(to)) for fro, to in settings.CHARACTER_TRANSLATIONS)

translation.activate(settings.SMS_LANGUAGE_CODE)

RANGE_ERROR = _('Invalid response(s) for question(s): "%(attributes)s". You sent: %(text)s')
ATTRIBUTE_ERROR = _('Unknown question codes: "%(attributes)s". You sent: %(text)s')
UNKNOWN_OBSERVER = _('Observer ID not found. Please resend with valid Observer ID. You sent: %(text)s')
INVALID_MESSAGE = _('Invalid message: "%(message)s". Please check and resend!')
SUBMISSION_RECEIVED = _('Thank you! Your report was received! You sent: %(message)s')


class App(AppBase):
    @reversion.create_revision()
    def handle(self, message):        
        temp = unicode(message.text)
        # strip all unwanted whitespace and punctuation marks
        at_position = temp.find('@')
        temp = filter(lambda s: s not in PUNCTUATIONS, temp[:at_position]).translate(TRANS_TABLE) + temp[at_position:] \
            if at_position != -1 else filter(lambda s: s not in PUNCTUATIONS, temp).translate(TRANS_TABLE)

        at_position = temp.find('@')
        working_text = temp[:at_position] if at_position != -1 else temp
        comment = temp[at_position + 1:] if at_position != -1 else None

        try:
            submission, observer = Form.parse(working_text)
            if not observer:
                message.respond(UNKNOWN_OBSERVER % {'text': message.text})
                return True
            else:
                # update the observer's last known connection
                observer.last_connection = message.connection
                observer.save()

                # Find submission for observer and persist valid data
                try:
                    activity = Activity.for_today()

                    try:
                        if submission['form'].autocreate_submission:
                            entry = Submission.objects.create(observer=observer, date=datetime.now().date(),
                                form=submission['form'], location=observer.location)
                        else:
                            try:
                                entry = Submission.objects.get(observer=observer, form=submission['form'],
                                    date__range=(activity.start_date, activity.end_date))
                            except Submission.MultipleObjectsReturned:
                                entry = Submission.objects.filter(observer=observer, form=submission['form'],
                                    date__range=(activity.start_date, activity.end_date)).order_by('date')[0]
                        entry.data.update(submission['data'])
                        entry.save()

                        # If there's a comment, save it
                        if comment:
                            # the comment field stores additional location information
                            # for incidents
                            if submission['form'].type == 'INCIDENT':
                                entry.data.update({'location': comment})
                                entry.save()
                            else:
                                Comment.objects.create(content_object=entry,
                                    user_name=observer.name or observer.observer_id, site=Site.objects.get_current(),
                                    comment=comment, submit_date=datetime.now())
                    except Submission.DoesNotExist:
                        pass
                except Activity.DoesNotExist:
                    pass

                if 'range_error_fields' in submission and submission['range_error_fields']:
                    message.respond(RANGE_ERROR % \
                        {'attributes': ', '.join(submission['range_error_fields']), 'text': message.text})
                    return True
                elif 'attribute_error_fields' in submission and submission['attribute_error_fields']:
                    message.respond(ATTRIBUTE_ERROR % \
                        {'attributes': ', '.join(submission['attribute_error_fields']), 'text': message.text})
                    return True
                else:
                    message.respond(SUBMISSION_RECEIVED % {'message': message.text})
                    return True
        except Form.DoesNotExist:
            # We couldn't parse the message hence it's invalid
            return self.default(message)

    def default(self, message):
        message.respond(INVALID_MESSAGE % {'message': message.text})
        return True
