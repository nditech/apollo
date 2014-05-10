from flask import current_app


def get_offset(multidict):
    try:
        offset = int(multidict.get('offset', 0))
    except ValueError:
        offset = 0

    return offset


def get_limit(multidict):
    page_size = current_app.config.get('PAGE_SIZE')
    try:
        limit = int(multidict.get('limit', page_size))
    except ValueError:
        limit = page_size

    return limit
