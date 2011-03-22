# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'EDAYChecklistAuditLogEntry.EA'
        db.add_column('psc_edaychecklistauditlogentry', 'EA', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EB'
        db.add_column('psc_edaychecklistauditlogentry', 'EB', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EC'
        db.add_column('psc_edaychecklistauditlogentry', 'EC', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.ED'
        db.add_column('psc_edaychecklistauditlogentry', 'ED', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EE'
        db.add_column('psc_edaychecklistauditlogentry', 'EE', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EF'
        db.add_column('psc_edaychecklistauditlogentry', 'EF', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EG'
        db.add_column('psc_edaychecklistauditlogentry', 'EG', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EH'
        db.add_column('psc_edaychecklistauditlogentry', 'EH', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EJ'
        db.add_column('psc_edaychecklistauditlogentry', 'EJ', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EK'
        db.add_column('psc_edaychecklistauditlogentry', 'EK', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EM'
        db.add_column('psc_edaychecklistauditlogentry', 'EM', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EN'
        db.add_column('psc_edaychecklistauditlogentry', 'EN', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EP'
        db.add_column('psc_edaychecklistauditlogentry', 'EP', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EQ'
        db.add_column('psc_edaychecklistauditlogentry', 'EQ', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.ER'
        db.add_column('psc_edaychecklistauditlogentry', 'ER', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.ES'
        db.add_column('psc_edaychecklistauditlogentry', 'ES', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.ET'
        db.add_column('psc_edaychecklistauditlogentry', 'ET', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EU'
        db.add_column('psc_edaychecklistauditlogentry', 'EU', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EV'
        db.add_column('psc_edaychecklistauditlogentry', 'EV', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EW'
        db.add_column('psc_edaychecklistauditlogentry', 'EW', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EX'
        db.add_column('psc_edaychecklistauditlogentry', 'EX', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EY'
        db.add_column('psc_edaychecklistauditlogentry', 'EY', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.EZ'
        db.add_column('psc_edaychecklistauditlogentry', 'EZ', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.FA'
        db.add_column('psc_edaychecklistauditlogentry', 'FA', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.FB'
        db.add_column('psc_edaychecklistauditlogentry', 'FB', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.FC'
        db.add_column('psc_edaychecklistauditlogentry', 'FC', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.FD'
        db.add_column('psc_edaychecklistauditlogentry', 'FD', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.FE'
        db.add_column('psc_edaychecklistauditlogentry', 'FE', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.FF'
        db.add_column('psc_edaychecklistauditlogentry', 'FF', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklistAuditLogEntry.FG'
        db.add_column('psc_edaychecklistauditlogentry', 'FG', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EA'
        db.add_column('psc_edaychecklist', 'EA', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EB'
        db.add_column('psc_edaychecklist', 'EB', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EC'
        db.add_column('psc_edaychecklist', 'EC', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.ED'
        db.add_column('psc_edaychecklist', 'ED', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EE'
        db.add_column('psc_edaychecklist', 'EE', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EF'
        db.add_column('psc_edaychecklist', 'EF', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EG'
        db.add_column('psc_edaychecklist', 'EG', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EH'
        db.add_column('psc_edaychecklist', 'EH', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EJ'
        db.add_column('psc_edaychecklist', 'EJ', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EK'
        db.add_column('psc_edaychecklist', 'EK', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EM'
        db.add_column('psc_edaychecklist', 'EM', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EN'
        db.add_column('psc_edaychecklist', 'EN', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EP'
        db.add_column('psc_edaychecklist', 'EP', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EQ'
        db.add_column('psc_edaychecklist', 'EQ', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.ER'
        db.add_column('psc_edaychecklist', 'ER', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.ES'
        db.add_column('psc_edaychecklist', 'ES', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.ET'
        db.add_column('psc_edaychecklist', 'ET', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EU'
        db.add_column('psc_edaychecklist', 'EU', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EV'
        db.add_column('psc_edaychecklist', 'EV', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EW'
        db.add_column('psc_edaychecklist', 'EW', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EX'
        db.add_column('psc_edaychecklist', 'EX', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EY'
        db.add_column('psc_edaychecklist', 'EY', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.EZ'
        db.add_column('psc_edaychecklist', 'EZ', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.FA'
        db.add_column('psc_edaychecklist', 'FA', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.FB'
        db.add_column('psc_edaychecklist', 'FB', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.FC'
        db.add_column('psc_edaychecklist', 'FC', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.FD'
        db.add_column('psc_edaychecklist', 'FD', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.FE'
        db.add_column('psc_edaychecklist', 'FE', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.FF'
        db.add_column('psc_edaychecklist', 'FF', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)

        # Adding field 'EDAYChecklist.FG'
        db.add_column('psc_edaychecklist', 'FG', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'EDAYChecklistAuditLogEntry.EA'
        db.delete_column('psc_edaychecklistauditlogentry', 'EA')

        # Deleting field 'EDAYChecklistAuditLogEntry.EB'
        db.delete_column('psc_edaychecklistauditlogentry', 'EB')

        # Deleting field 'EDAYChecklistAuditLogEntry.EC'
        db.delete_column('psc_edaychecklistauditlogentry', 'EC')

        # Deleting field 'EDAYChecklistAuditLogEntry.ED'
        db.delete_column('psc_edaychecklistauditlogentry', 'ED')

        # Deleting field 'EDAYChecklistAuditLogEntry.EE'
        db.delete_column('psc_edaychecklistauditlogentry', 'EE')

        # Deleting field 'EDAYChecklistAuditLogEntry.EF'
        db.delete_column('psc_edaychecklistauditlogentry', 'EF')

        # Deleting field 'EDAYChecklistAuditLogEntry.EG'
        db.delete_column('psc_edaychecklistauditlogentry', 'EG')

        # Deleting field 'EDAYChecklistAuditLogEntry.EH'
        db.delete_column('psc_edaychecklistauditlogentry', 'EH')

        # Deleting field 'EDAYChecklistAuditLogEntry.EJ'
        db.delete_column('psc_edaychecklistauditlogentry', 'EJ')

        # Deleting field 'EDAYChecklistAuditLogEntry.EK'
        db.delete_column('psc_edaychecklistauditlogentry', 'EK')

        # Deleting field 'EDAYChecklistAuditLogEntry.EM'
        db.delete_column('psc_edaychecklistauditlogentry', 'EM')

        # Deleting field 'EDAYChecklistAuditLogEntry.EN'
        db.delete_column('psc_edaychecklistauditlogentry', 'EN')

        # Deleting field 'EDAYChecklistAuditLogEntry.EP'
        db.delete_column('psc_edaychecklistauditlogentry', 'EP')

        # Deleting field 'EDAYChecklistAuditLogEntry.EQ'
        db.delete_column('psc_edaychecklistauditlogentry', 'EQ')

        # Deleting field 'EDAYChecklistAuditLogEntry.ER'
        db.delete_column('psc_edaychecklistauditlogentry', 'ER')

        # Deleting field 'EDAYChecklistAuditLogEntry.ES'
        db.delete_column('psc_edaychecklistauditlogentry', 'ES')

        # Deleting field 'EDAYChecklistAuditLogEntry.ET'
        db.delete_column('psc_edaychecklistauditlogentry', 'ET')

        # Deleting field 'EDAYChecklistAuditLogEntry.EU'
        db.delete_column('psc_edaychecklistauditlogentry', 'EU')

        # Deleting field 'EDAYChecklistAuditLogEntry.EV'
        db.delete_column('psc_edaychecklistauditlogentry', 'EV')

        # Deleting field 'EDAYChecklistAuditLogEntry.EW'
        db.delete_column('psc_edaychecklistauditlogentry', 'EW')

        # Deleting field 'EDAYChecklistAuditLogEntry.EX'
        db.delete_column('psc_edaychecklistauditlogentry', 'EX')

        # Deleting field 'EDAYChecklistAuditLogEntry.EY'
        db.delete_column('psc_edaychecklistauditlogentry', 'EY')

        # Deleting field 'EDAYChecklistAuditLogEntry.EZ'
        db.delete_column('psc_edaychecklistauditlogentry', 'EZ')

        # Deleting field 'EDAYChecklistAuditLogEntry.FA'
        db.delete_column('psc_edaychecklistauditlogentry', 'FA')

        # Deleting field 'EDAYChecklistAuditLogEntry.FB'
        db.delete_column('psc_edaychecklistauditlogentry', 'FB')

        # Deleting field 'EDAYChecklistAuditLogEntry.FC'
        db.delete_column('psc_edaychecklistauditlogentry', 'FC')

        # Deleting field 'EDAYChecklistAuditLogEntry.FD'
        db.delete_column('psc_edaychecklistauditlogentry', 'FD')

        # Deleting field 'EDAYChecklistAuditLogEntry.FE'
        db.delete_column('psc_edaychecklistauditlogentry', 'FE')

        # Deleting field 'EDAYChecklistAuditLogEntry.FF'
        db.delete_column('psc_edaychecklistauditlogentry', 'FF')

        # Deleting field 'EDAYChecklistAuditLogEntry.FG'
        db.delete_column('psc_edaychecklistauditlogentry', 'FG')

        # Deleting field 'EDAYChecklist.EA'
        db.delete_column('psc_edaychecklist', 'EA')

        # Deleting field 'EDAYChecklist.EB'
        db.delete_column('psc_edaychecklist', 'EB')

        # Deleting field 'EDAYChecklist.EC'
        db.delete_column('psc_edaychecklist', 'EC')

        # Deleting field 'EDAYChecklist.ED'
        db.delete_column('psc_edaychecklist', 'ED')

        # Deleting field 'EDAYChecklist.EE'
        db.delete_column('psc_edaychecklist', 'EE')

        # Deleting field 'EDAYChecklist.EF'
        db.delete_column('psc_edaychecklist', 'EF')

        # Deleting field 'EDAYChecklist.EG'
        db.delete_column('psc_edaychecklist', 'EG')

        # Deleting field 'EDAYChecklist.EH'
        db.delete_column('psc_edaychecklist', 'EH')

        # Deleting field 'EDAYChecklist.EJ'
        db.delete_column('psc_edaychecklist', 'EJ')

        # Deleting field 'EDAYChecklist.EK'
        db.delete_column('psc_edaychecklist', 'EK')

        # Deleting field 'EDAYChecklist.EM'
        db.delete_column('psc_edaychecklist', 'EM')

        # Deleting field 'EDAYChecklist.EN'
        db.delete_column('psc_edaychecklist', 'EN')

        # Deleting field 'EDAYChecklist.EP'
        db.delete_column('psc_edaychecklist', 'EP')

        # Deleting field 'EDAYChecklist.EQ'
        db.delete_column('psc_edaychecklist', 'EQ')

        # Deleting field 'EDAYChecklist.ER'
        db.delete_column('psc_edaychecklist', 'ER')

        # Deleting field 'EDAYChecklist.ES'
        db.delete_column('psc_edaychecklist', 'ES')

        # Deleting field 'EDAYChecklist.ET'
        db.delete_column('psc_edaychecklist', 'ET')

        # Deleting field 'EDAYChecklist.EU'
        db.delete_column('psc_edaychecklist', 'EU')

        # Deleting field 'EDAYChecklist.EV'
        db.delete_column('psc_edaychecklist', 'EV')

        # Deleting field 'EDAYChecklist.EW'
        db.delete_column('psc_edaychecklist', 'EW')

        # Deleting field 'EDAYChecklist.EX'
        db.delete_column('psc_edaychecklist', 'EX')

        # Deleting field 'EDAYChecklist.EY'
        db.delete_column('psc_edaychecklist', 'EY')

        # Deleting field 'EDAYChecklist.EZ'
        db.delete_column('psc_edaychecklist', 'EZ')

        # Deleting field 'EDAYChecklist.FA'
        db.delete_column('psc_edaychecklist', 'FA')

        # Deleting field 'EDAYChecklist.FB'
        db.delete_column('psc_edaychecklist', 'FB')

        # Deleting field 'EDAYChecklist.FC'
        db.delete_column('psc_edaychecklist', 'FC')

        # Deleting field 'EDAYChecklist.FD'
        db.delete_column('psc_edaychecklist', 'FD')

        # Deleting field 'EDAYChecklist.FE'
        db.delete_column('psc_edaychecklist', 'FE')

        # Deleting field 'EDAYChecklist.FF'
        db.delete_column('psc_edaychecklist', 'FF')

        # Deleting field 'EDAYChecklist.FG'
        db.delete_column('psc_edaychecklist', 'FG')


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
        'psc.access': {
            'Meta': {'object_name': 'Access'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'psc.contesting': {
            'Meta': {'object_name': 'Contesting'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'party': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Party']"}),
            'state': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.State']"})
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
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
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
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_dcochecklist_audit_log_entry'"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
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
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
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
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_dcoincident_audit_log_entry'"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
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
        'psc.edaychecklist': {
            'AA': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BC': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BF': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BH': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BJ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BK': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BM': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BN': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BP': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CB': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CF': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CG': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CH': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CJ': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CK': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CM': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CN': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CP': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CQ': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'DA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DF': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DH': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ED': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EF': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EH': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EJ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EK': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EM': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EN': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EP': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EQ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ER': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ES': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ET': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EU': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EV': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EW': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EX': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EY': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EZ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FF': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'object_name': 'EDAYChecklist'},
            'checklist_index': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '1', 'db_index': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'psc.edaychecklistauditlogentry': {
            'AA': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BC': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BF': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BH': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BJ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BK': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BM': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'BN': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'BP': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CB': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'CF': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CG': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CH': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CJ': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CK': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CM': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CN': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CP': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'CQ': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'DA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DF': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'DH': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ED': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EF': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EH': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EJ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EK': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EM': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EN': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EP': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EQ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ER': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ES': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ET': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EU': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EV': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EW': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EX': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EY': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'EZ': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FA': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FB': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FC': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FD': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FE': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FF': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'FG': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'Meta': {'ordering': "('-action_date',)", 'object_name': 'EDAYChecklistAuditLogEntry'},
            'action_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'action_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_edaychecklist_audit_log_entry'"}),
            'checklist_index': ('django.db.models.fields.CharField', [], {'default': "'1'", 'max_length': '1', 'db_index': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'psc.edaychecklistoverrides': {
            'Meta': {'object_name': 'EDAYChecklistOverrides'},
            'checklist': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.EDAYChecklist']"}),
            'field': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'psc.edayincident': {
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
            'Meta': {'object_name': 'EDAYIncident'},
            'N': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'P': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Q': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'R': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'S': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'T': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"})
        },
        'psc.edayincidentauditlogentry': {
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
            'Meta': {'ordering': "('-action_date',)", 'object_name': 'EDAYIncidentAuditLogEntry'},
            'N': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'P': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'Q': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'R': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'S': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'T': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'action_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'action_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'action_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_edayincident_audit_log_entry'"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"})
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
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer_id': ('django.db.models.fields.CharField', [], {'max_length': '6', 'db_index': 'True'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'observers'", 'to': "orm['psc.Partner']"}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '14', 'null': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'supervisor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'observers'", 'null': 'True', 'to': "orm['psc.Observer']"})
        },
        'psc.partner': {
            'Meta': {'object_name': 'Partner'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'psc.party': {
            'Meta': {'object_name': 'Party'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': "'true'", 'blank': "'true'"})
        },
        'psc.registrationcenter': {
            'Meta': {'object_name': 'RegistrationCenter'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inec_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.LGA']", 'null': 'True', 'blank': 'True'})
        },
        'psc.sample': {
            'Meta': {'object_name': 'Sample'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'sample'", 'to': "orm['psc.RegistrationCenter']"}),
            'sample': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'})
        },
        'psc.state': {
            'Meta': {'ordering': "['name']", 'object_name': 'State'},
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
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verified_second': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verified_third': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_vrchecklist_audit_log_entry'"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'location_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['psc.Observer']"}),
            'report_rc': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'report_rcid': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'submitted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verified_second': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verified_third': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
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
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
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
            'action_user': ('audit_log.models.fields.LastUserField', [], {'related_name': "'_vrincident_audit_log_entry'"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'db_index': 'True'}),
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
