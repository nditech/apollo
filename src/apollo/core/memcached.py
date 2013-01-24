'''
BigMemcached cache backend
==========================

Memcached is capable of storing values that are bigger than 1MB.
The default django memcached backend doesn't support storing 
values larger than that original limit. The BigMemcached backend 
provides the additional functionality to allow storage of bigger 
values by providing a configuration option that can be exploited 
to enable this.

CACHES = {
    'default': {
        'BACKEND': 'memcached.BigMemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'OPTIONS': {
            'MAX_VALUE_LENGTH': 2 * 1024 * 1024 # 2MB
        }
    }
}
'''
from django.core.cache.backends.memcached import MemcachedCache


class BigMemcachedCache(MemcachedCache):
    @property
    def _cache(self):
        """
        Implements transparent thread-safe access to a memcached client.
        """
        if getattr(self, '_client', None) is None:
            if getattr(self, '_options', None) and 'MAX_VALUE_LENGTH' in self._options:
                self._client = self._lib.Client(self._servers,
                    server_max_value_length=self._options['MAX_VALUE_LENGTH'])
            else:
                self._client = self._lib.Client(self._servers)

        return self._client
