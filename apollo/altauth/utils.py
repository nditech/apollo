def get_full_class_name(item):
    if isinstance(item, type):
        cls = item
    else:
        cls = item.__class__
    module = cls.__module__
    if module == str.__module__:
        return cls.__name__
    else:
        return '{}.{}'.format(module, cls.__name__)
