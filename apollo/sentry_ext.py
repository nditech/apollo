# -*- coding: utf-8 -*-
from flask import g
from raven.base import Client

from apollo import settings


class ApolloRavenClient(Client):
	def capture(self, *args, **kwargs):
		self.context.merge({
			u'event': getattr(g, u'event', None),
			u'apollo_version': getattr(settings, u'APOLLO_VERSION',
				u'Unspecified'),
		})

		super(ApolloRavenClient, self).capture(self, *args, **kwargs)
