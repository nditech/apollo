# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'LocationType'
        db.create_table('core_locationtype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=10, blank=True)),
            ('on_display', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('in_form', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('core', ['LocationType'])

        # Adding model 'Location'
        db.create_table('core_location', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.LocationType'])),
            ('data', self.gf('django_orm.postgresql.hstore.fields.DictionaryField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Location'])

        # Adding model 'Partner'
        db.create_table('core_partner', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('abbr', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('core', ['Partner'])

        # Adding model 'ObserverRole'
        db.create_table('core_observerrole', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, db_index=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ObserverRole'], null=True, blank=True)),
        ))
        db.send_create_signal('core', ['ObserverRole'])

        # Adding model 'Observer'
        db.create_table('core_observer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('observer_id', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('contact', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='observer', unique=True, null=True, to=orm['rapidsms.Contact'])),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.ObserverRole'])),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='observers', to=orm['core.Location'])),
            ('supervisor', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Observer'], null=True, blank=True)),
            ('gender', self.gf('django.db.models.fields.CharField')(db_index=True, max_length=1, null=True, blank=True)),
            ('partner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Partner'], null=True, blank=True)),
            ('data', self.gf('django_orm.postgresql.hstore.fields.DictionaryField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal('core', ['Observer'])

        # Adding model 'ObserverDataField'
        db.create_table('core_observerdatafield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('core', ['ObserverDataField'])

        # Adding model 'Form'
        db.create_table('core_form', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('type', self.gf('django.db.models.fields.CharField')(default='CHECKLIST', max_length=100)),
            ('trigger', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
            ('field_pattern', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('autocreate_submission', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('core', ['Form'])

        # Adding model 'FormGroup'
        db.create_table('core_formgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('abbr', self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(related_name='groups', to=orm['core.Form'])),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('core', ['FormGroup'])

        # Adding model 'FormField'
        db.create_table('core_formfield', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='fields', to=orm['core.FormGroup'])),
            ('tag', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('upper_limit', self.gf('django.db.models.fields.IntegerField')(default=9999, null=True)),
            ('lower_limit', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
            ('present_true', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('allow_multiple', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('core', ['FormField'])

        # Adding model 'VoteOption'
        db.create_table('core_voteoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(related_name='vote_options', to=orm['core.Form'])),
            ('field', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.FormField'])),
            ('abbr', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('core', ['VoteOption'])

        # Adding model 'FormFieldOption'
        db.create_table('core_formfieldoption', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('field', self.gf('django.db.models.fields.related.ForeignKey')(related_name='options', to=orm['core.FormField'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('option', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('core', ['FormFieldOption'])

        # Adding model 'Submission'
        db.create_table('core_submission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('form', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['core.Form'])),
            ('observer', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['core.Observer'], null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(related_name='submissions', to=orm['core.Location'])),
            ('date', self.gf('django.db.models.fields.DateField')(default=datetime.datetime(2013, 1, 24, 0, 0))),
            ('data', self.gf('django_orm.postgresql.hstore.fields.DictionaryField')(db_index=True, null=True, blank=True)),
            ('overrides', self.gf('django_orm.postgresql.hstore.fields.DictionaryField')(db_index=True, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('core', ['Submission'])


    def backwards(self, orm):
        # Deleting model 'LocationType'
        db.delete_table('core_locationtype')

        # Deleting model 'Location'
        db.delete_table('core_location')

        # Deleting model 'Partner'
        db.delete_table('core_partner')

        # Deleting model 'ObserverRole'
        db.delete_table('core_observerrole')

        # Deleting model 'Observer'
        db.delete_table('core_observer')

        # Deleting model 'ObserverDataField'
        db.delete_table('core_observerdatafield')

        # Deleting model 'Form'
        db.delete_table('core_form')

        # Deleting model 'FormGroup'
        db.delete_table('core_formgroup')

        # Deleting model 'FormField'
        db.delete_table('core_formfield')

        # Deleting model 'VoteOption'
        db.delete_table('core_voteoption')

        # Deleting model 'FormFieldOption'
        db.delete_table('core_formfieldoption')

        # Deleting model 'Submission'
        db.delete_table('core_submission')


    models = {
        'core.form': {
            'Meta': {'object_name': 'Form'},
            'autocreate_submission': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'field_pattern': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'trigger': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "'CHECKLIST'", 'max_length': '100'})
        },
        'core.formfield': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'FormField'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'allow_multiple': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'fields'", 'to': "orm['core.FormGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lower_limit': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'present_true': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tag': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'upper_limit': ('django.db.models.fields.IntegerField', [], {'default': '9999', 'null': 'True'})
        },
        'core.formfieldoption': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'FormFieldOption'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'field': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': "orm['core.FormField']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'core.formgroup': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'FormGroup'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'abbr': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'groups'", 'to': "orm['core.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'})
        },
        'core.location': {
            'Meta': {'ordering': "['name']", 'object_name': 'Location'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'data': ('django_orm.postgresql.hstore.fields.DictionaryField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.LocationType']"})
        },
        'core.locationtype': {
            'Meta': {'object_name': 'LocationType'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_form': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'on_display': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'core.observer': {
            'Meta': {'ordering': "['observer_id']", 'object_name': 'Observer'},
            'contact': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'observer'", 'unique': 'True', 'null': 'True', 'to': "orm['rapidsms.Contact']"}),
            'data': ('django_orm.postgresql.hstore.fields.DictionaryField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'observers'", 'to': "orm['core.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'observer_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'partner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Partner']", 'null': 'True', 'blank': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ObserverRole']"}),
            'supervisor': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Observer']", 'null': 'True', 'blank': 'True'})
        },
        'core.observerdatafield': {
            'Meta': {'object_name': 'ObserverDataField'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'core.observerrole': {
            'Meta': {'object_name': 'ObserverRole'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.ObserverRole']", 'null': 'True', 'blank': 'True'})
        },
        'core.partner': {
            'Meta': {'object_name': 'Partner'},
            'abbr': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.submission': {
            'Meta': {'object_name': 'Submission'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django_orm.postgresql.hstore.fields.DictionaryField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 1, 24, 0, 0)'}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['core.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['core.Location']"}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Observer']", 'null': 'True', 'blank': 'True'}),
            'overrides': ('django_orm.postgresql.hstore.fields.DictionaryField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'core.voteoption': {
            'Meta': {'object_name': 'VoteOption'},
            'abbr': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'field': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.FormField']"}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'vote_options'", 'to': "orm['core.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['core']