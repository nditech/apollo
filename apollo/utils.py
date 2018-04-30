# -*- coding: utf-8 -*-
import codecs
from datetime import datetime
import os
from uuid import UUID
import warnings

from pytz import utc


def read_env(env_path=None):
    if not os.path.exists(env_path):
        warnings.warn('No environment file found. Skipping load.')
        return

    for k, v in parse_env(env_path):
        os.environ.setdefault(k, v)


def parse_env(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            v = v.strip('"').strip("'")
            yield k, v


def current_timestamp():
    return utc.localize(datetime.utcnow())


def validate_uuid(uuid_string):
    try:
        UUID(uuid_string, version=4)
        return True
    except ValueError:
        return False


def remove_bom_in_place(path):
    buffer_size = 4096
    bom_length = len(codecs.BOM_UTF8)

    with open(path, 'r+b') as fp:
        chunk = fp.read(buffer_size)
        if chunk.startswith(codecs.BOM_UTF8):
            i = 0
            chunk = chunk[bom_length:]
            while chunk:
                fp.seek(i)
                fp.write(chunk)
                i += len(chunk)
                fp.seek(bom_length, os.SEEK_CUR)
                chunk = fp.read(buffer_size)
            fp.seek(-bom_length, os.SEEK_CUR)
            fp.truncate()


def strip_bom_header(fileobj):
    chunk_size = 512
    chunk = fileobj.read(chunk_size)

    if chunk.startswith(codecs.BOM_UTF8):
        fileobj.seek(len(codecs.BOM_UTF8))
    else:
        fileobj.seek(0)
