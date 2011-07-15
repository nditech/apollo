def model_attribute_cache(f):
    def doCache(*args, **kwargs):
        obj = args[0]
        cache_key = '_%s' % f.__name__
        if not hasattr(obj, cache_key):
            setattr(obj, cache_key, f(*args, **kwargs))
        return getattr(obj, cache_key)
    return doCache
