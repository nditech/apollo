# -*- coding: utf-8 -*-
import abc


class ArchiveSerializer(abc.ABC):
    @abc.abstractmethod
    def serialize(self, obj, zip_file):
        pass

    @abc.abstractmethod
    def deserialize(self, zip_file):
        pass
