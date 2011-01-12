# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Zone'
        db.create_table('psc_zone', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, blank=True)),
        ))
        db.send_create_signal('psc', ['Zone'])

        # Adding model 'State'
        db.create_table('psc_state', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='states', null=True, to=orm['psc.Zone'])),
        ))
        db.send_create_signal('psc', ['State'])

        # Adding model 'District'
        db.create_table('psc_district', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='districts', null=True, to=orm['psc.State'])),
        ))
        db.send_create_signal('psc', ['District'])

        # Adding model 'LGA'
        db.create_table('psc_lga', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='lgas', null=True, to=orm['psc.District'])),
        ))
        db.send_create_signal('psc', ['LGA'])

        # Adding model 'Ward'
        db.create_table('psc_ward', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=50, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='wards', null=True, to=orm['psc.LGA'])),
        ))
        db.send_create_signal('psc', ['Ward'])

        # Adding model 'RegistrationCenter'
        db.create_table('psc_registrationcenter', (
            ('location_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['locations.Location'], unique=True, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
        ))
        db.send_create_signal('psc', ['RegistrationCenter'])

        # Adding model 'Partner'
        db.create_table('psc_partner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('psc', ['Partner'])

        # Adding model 'Observer'
        db.create_table('psc_observer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contact', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['rapidsms.Contact'], unique=True, null=True, blank=True)),
            ('dob', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('phone', self.gf('django.db.models.fields.CharField')(max_length=14, null=True, blank=True)),
            ('observer_id', self.gf('django.db.models.fields.CharField')(max_length=6)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('supervisor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='observers', null=True, to=orm['psc.Observer'])),
            ('partner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='observers', to=orm['psc.Partner'])),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=3, blank=True)),
        ))
        db.send_create_signal('psc', ['Observer'])

        # Adding model 'VRChecklistAuditLogEntry'
        db.create_table('psc_vrchecklistauditlogentry', (
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True, blank=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('A', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('B', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('C', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('D1', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D2', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D3', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D4', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E1', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E2', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E3', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E4', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E5', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('H', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('J', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('M', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('N', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('P', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('Q', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('R', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('S', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('T', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('U', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('V', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('W', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('X', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('Y', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('Z', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('AA', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('submitted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('report_rc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('report_rcid', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('action_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('action_user', self.gf('audit_log.models.fields.LastUserField')(related_name='_vrchecklist_audit_log_entry', null=True, to=orm['auth.User'])),
            ('action_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('psc', ['VRChecklistAuditLogEntry'])

        # Adding model 'VRChecklist'
        db.create_table('psc_vrchecklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('A', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('B', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('C', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('D1', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D2', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D3', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D4', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E1', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E2', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E3', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E4', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E5', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('H', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('J', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('M', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('N', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('P', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('Q', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('R', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('S', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('T', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('U', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('V', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('W', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('X', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('Y', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('Z', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('AA', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('submitted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('report_rc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('report_rcid', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
        ))
        db.send_create_signal('psc', ['VRChecklist'])

        # Adding model 'VRIncidentAuditLogEntry'
        db.create_table('psc_vrincidentauditlogentry', (
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True, blank=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('A', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('B', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('C', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('H', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('J', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('M', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('N', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('P', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('Q', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('action_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('action_user', self.gf('audit_log.models.fields.LastUserField')(related_name='_vrincident_audit_log_entry', null=True, to=orm['auth.User'])),
            ('action_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('psc', ['VRIncidentAuditLogEntry'])

        # Adding model 'VRIncident'
        db.create_table('psc_vrincident', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('A', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('B', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('C', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('H', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('J', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('M', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('N', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('P', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('Q', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('psc', ['VRIncident'])

        # Adding model 'DCOChecklistAuditLogEntry'
        db.create_table('psc_dcochecklistauditlogentry', (
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True, blank=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('sms_serial', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('A', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('B', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('C', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('D', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('E', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('F1', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F2', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F3', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F4', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F5', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F6', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F7', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F8', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F9', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('H', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('J', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('M', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('N', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('P', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('Q', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('R', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('S', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('T', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('U', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('V', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('W', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('X', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('submitted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('report_rc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('report_rcid', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('action_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('action_user', self.gf('audit_log.models.fields.LastUserField')(related_name='_dcochecklist_audit_log_entry', null=True, to=orm['auth.User'])),
            ('action_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('psc', ['DCOChecklistAuditLogEntry'])

        # Adding model 'DCOChecklist'
        db.create_table('psc_dcochecklist', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('sms_serial', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('A', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('B', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('C', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('D', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('E', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('F1', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F2', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F3', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F4', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F5', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F6', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F7', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F8', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F9', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('H', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('J', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('M', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('N', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('P', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('Q', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('R', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, blank=True)),
            ('S', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('T', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('U', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('V', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('W', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('X', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('submitted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('report_rc', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('report_rcid', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
        ))
        db.send_create_signal('psc', ['DCOChecklist'])

        # Adding model 'DCOIncidentAuditLogEntry'
        db.create_table('psc_dcoincidentauditlogentry', (
            ('id', self.gf('django.db.models.fields.IntegerField')(db_index=True, blank=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('A', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('B', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('C', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('H', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('J', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('action_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('action_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('action_user', self.gf('audit_log.models.fields.LastUserField')(related_name='_dcoincident_audit_log_entry', null=True, to=orm['auth.User'])),
            ('action_type', self.gf('django.db.models.fields.CharField')(max_length=1)),
        ))
        db.send_create_signal('psc', ['DCOIncidentAuditLogEntry'])

        # Adding model 'DCOIncident'
        db.create_table('psc_dcoincident', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('location_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'], null=True, blank=True)),
            ('location_id', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['psc.Observer'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('A', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('B', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('C', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('D', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('E', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('F', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('G', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('H', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('J', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('K', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('psc', ['DCOIncident'])


    def backwards(self, orm):
        
        # Deleting model 'Zone'
        db.delete_table('psc_zone')

        # Deleting model 'State'
        db.delete_table('psc_state')

        # Deleting model 'District'
        db.delete_table('psc_district')

        # Deleting model 'LGA'
        db.delete_table('psc_lga')

        # Deleting model 'Ward'
        db.delete_table('psc_ward')

        # Deleting model 'RegistrationCenter'
        db.delete_table('psc_registrationcenter')

        # Deleting model 'Partner'
        db.delete_table('psc_partner')

        # Deleting model 'Observer'
        db.delete_table('psc_observer')

        # Deleting model 'VRChecklistAuditLogEntry'
        db.delete_table('psc_vrchecklistauditlogentry')

        # Deleting model 'VRChecklist'
        db.delete_table('psc_vrchecklist')

        # Deleting model 'VRIncidentAuditLogEntry'
        db.delete_table('psc_vrincidentauditlogentry')

        # Deleting model 'VRIncident'
        db.delete_table('psc_vrincident')

        # Deleting model 'DCOChecklistAuditLogEntry'
        db.delete_table('psc_dcochecklistauditlogentry')

        # Deleting model 'DCOChecklist'
        db.delete_table('psc_dcochecklist')

        # Deleting model 'DCOIncidentAuditLogEntry'
        db.delete_table('psc_dcoincidentauditlogentry')

        # Deleting model 'DCOIncident'
        db.delete_table('psc_dcoincident')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'locations.location': {
            'Meta': {'object_name': 'Location'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'parent_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'point': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['locations.Point']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'locations'", 'null': 'True', 'to': "orm['locations.LocationType']"})
        },
        'locations.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'primary_key': 'True', 'db_index': 'True'})
        },
        'locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        },
        'psc.dcochecklist': {
            'A': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'B': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'C': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'D': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'E': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'F1': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F2': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F3': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F4': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F5': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F6': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F7': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F8': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F9': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'H': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'J': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'M': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'Meta': {'object_name': 'DCOChecklist'},
            'N': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'P': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'Q': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'R': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'S': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'T': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'U': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'V': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'W': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'X': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'sms_serial': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'psc.dcochecklistauditlogentry': {
            'A': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'B': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'C': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'D': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'E': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'F1': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F2': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F3': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F4': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F5': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F6': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F7': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F8': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F9': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'H': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'J': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'M': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'Meta': {'ordering': "('-action_date',)", 'object_name': 'DCOChecklistAuditLogEntry'},
            'N': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'P': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'Q': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'R': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'S': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'T': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'U': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'V': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'W': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'X': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'action_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'action_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_dcochecklist_audit_log_entry'", 'null': 'True', 'to': "orm['auth.User']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'sms_serial': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'psc.dcoincident': {
            'A': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'B': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'C': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'H': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'J': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'DCOIncident'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"})
        },
        'psc.dcoincidentauditlogentry': {
            'A': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'B': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'C': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'H': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'J': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'ordering': "('-action_date',)", 'object_name': 'DCOIncidentAuditLogEntry'},
            'action_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'action_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_dcoincident_audit_log_entry'", 'null': 'True', 'to': "orm['auth.User']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"})
        },
        'psc.district': {
            'Meta': {'object_name': 'District'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'districts'", 'null': 'True', 'to': "orm['psc.State']"})
        },
        'psc.lga': {
            'Meta': {'object_name': 'LGA'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'lgas'", 'null': 'True', 'to': "orm['psc.District']"})
        },
        'psc.observer': {
            'Meta': {'object_name': 'Observer'},
            'contact': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['rapidsms.Contact']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer_id': ('django.db.models.fields.CharField', [], {'max_length': '6'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'observers'", 'to': "orm['psc.Partner']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'supervisor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'observers'", 'null': 'True', 'to': "orm['psc.Observer']"})
        },
        'psc.partner': {
            'Meta': {'object_name': 'Partner'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'psc.registrationcenter': {
            'Meta': {'object_name': 'RegistrationCenter', '_ormbases': ['locations.Location']},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'location_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['locations.Location']", 'unique': 'True', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'psc.state': {
            'Meta': {'object_name': 'State'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'states'", 'null': 'True', 'to': "orm['psc.Zone']"})
        },
        'psc.vrchecklist': {
            'A': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'AA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'B': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'C': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'D1': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D2': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D3': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D4': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E1': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E2': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E3': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E4': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E5': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'H': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'J': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'M': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'VRChecklist'},
            'N': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'P': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Q': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'R': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'S': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'T': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'U': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'V': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'W': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'X': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'Y': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Z': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'psc.vrchecklistauditlogentry': {
            'A': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'AA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'B': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'C': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'D1': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D2': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D3': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D4': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E1': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E2': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E3': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E4': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E5': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'H': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'J': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'M': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'ordering': "('-action_date',)", 'object_name': 'VRChecklistAuditLogEntry'},
            'N': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'P': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Q': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'R': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'S': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'T': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'U': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'V': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'W': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'X': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'blank': 'True'}),
            'Y': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Z': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'action_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'action_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_vrchecklist_audit_log_entry'", 'null': 'True', 'to': "orm['auth.User']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'psc.vrincident': {
            'A': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'B': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'C': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'H': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'J': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'M': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'VRIncident'},
            'N': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'P': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Q': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"})
        },
        'psc.vrincidentauditlogentry': {
            'A': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'B': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'C': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'D': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'E': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'F': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'G': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'H': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'J': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'K': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'M': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'ordering': "('-action_date',)", 'object_name': 'VRIncidentAuditLogEntry'},
            'N': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'P': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Q': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'action_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'action_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_vrincident_audit_log_entry'", 'null': 'True', 'to': "orm['auth.User']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"})
        },
        'psc.ward': {
            'Meta': {'object_name': 'Ward'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'wards'", 'null': 'True', 'to': "orm['psc.LGA']"})
        },
        'psc.zone': {
            'Meta': {'object_name': 'Zone'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['psc']
