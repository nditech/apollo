# -*- coding: utf-8 -*-
class Service(object):
    '''Database service wrapper class'''
    __model__ = None

    def _isinstance(self, model, raise_error=True):
        rv = isinstance(model, self.__model__)
        if not rv and raise_error:
            raise ValueError(f'{model} is not of type {self.__model__}')

        return rv

    def save(self, model, commit=True):
        return model.save(commit)

    def find(self, **kwargs):
        return self.__model__.query.filter_by(**kwargs)

    def all(self):
        return self.__model__.query.all()

    def get(self, **kwargs):
        return self.find(**kwargs).one_or_none()

    def get_or_404(self, **kwargs):
        rv = self.get(**kwargs)
        if rv is None:
            abort(404)

        return rv

    def first(self, **kwargs):
        return self.find(**kwargs).first()

    def new(self, **kwargs):
        return self.__model__(**kwargs)

    def create(self, **kwargs):
        return self.save(self.new(**kwargs))

    def get_or_create(self, **kwargs):
        return self.get(**kwargs) or self.create(**kwargs)

    def update(self, model, commit=True, **kwargs):
        self._isinstance(model)
        return model.update(commit=commit, **kwargs)

    def delete(self, model, commit=True):
        self._isinstance(model)
        return model.delete(commit=commit)
