# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Observer.last_connection'
        db.add_column('core_observer', 'last_connection',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['rapidsms.Connection'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Observer.last_connection'
        db.delete_column('core_observer', 'last_connection_id')


    models = {
        'core.activity': {
            'Meta': {'object_name': 'Activity'},
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 3, 10, 0, 0)'}),
            'forms': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'activities'", 'symmetrical': 'False', 'to': "orm['core.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
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
            'Meta': {'object_name': 'Location'},
            'code': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '100', 'blank': 'True'}),
            'data': ('djorm_hstore.fields.DictionaryField', [], {'default': '{}', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
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
            'data': ('djorm_hstore.fields.DictionaryField', [], {'default': '{}', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']", 'null': 'True', 'blank': 'True'}),
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
        'core.sample': {
            'Meta': {'object_name': 'Sample'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locations': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'samples'", 'symmetrical': 'False', 'to': "orm['core.Location']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'core.submission': {
            'Meta': {'object_name': 'Submission'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('djorm_hstore.fields.DictionaryField', [], {'default': '{}', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2013, 3, 10, 0, 0)'}),
            'form': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['core.Form']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'submissions'", 'to': "orm['core.Location']"}),
            'master': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Submission']", 'null': 'True', 'blank': 'True'}),
            'observer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['core.Observer']", 'null': 'True', 'blank': 'True'}),
            'overrides': ('djorm_hstore.fields.DictionaryField', [], {'default': '{}', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
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
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'unique_together': "(('backend', 'identity'),)", 'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['core']