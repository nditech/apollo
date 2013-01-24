# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MessageLog'
        db.create_table('messagelog_messagelog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('mobile', self.gf('django.db.models.fields.CharField')(max_length=16, db_index=True)),
            ('text', self.gf('django.db.models.fields.TextField')(db_index=True)),
            ('direction', self.gf('django.db.models.fields.SmallIntegerField')(db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, db_index=True, blank=True)),
            ('delivered', self.gf('django.db.models.fields.DateTimeField')(db_index=True, null=True, blank=True)),
        ))
        db.send_create_signal('messagelog', ['MessageLog'])


    def backwards(self, orm):
        # Deleting model 'MessageLog'
        db.delete_table('messagelog_messagelog')


    models = {
        'messagelog.messagelog': {
            'Meta': {'object_name': 'MessageLog'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'delivered': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True', 'null': 'True', 'blank': 'True'}),
            'direction': ('django.db.models.fields.SmallIntegerField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '16', 'db_index': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['messagelog']