# -*- coding: utf-8 -*-
import codecs
from datetime import datetime
from uuid import UUID, uuid4

from PIL import Image
from pytz import utc


def current_timestamp():
    """Gets the current timestamp with the timezone information."""
    return utc.localize(datetime.utcnow())


def validate_uuid(uuid_string):
    """Validates a uuid4 string."""
    try:
        UUID(uuid_string, version=4)
        return True
    except ValueError:
        return False


def strip_bom_header(fileobj):
    """Strips the byte-order mark from the header of a file."""
    chunk_size = 512
    chunk = fileobj.read(chunk_size)

    if chunk.startswith(codecs.BOM_UTF8):
        fileobj.seek(len(codecs.BOM_UTF8))
    else:
        fileobj.seek(0)

    return fileobj


def generate_identifier():
    """Generate an identifier with a maximum value of 0xffffffffffff."""
    val = int(uuid4()) % 281474976710656
    padded = f"{val:#012x}"
    return padded[2:]


def resize_image(pil_image: Image, new_size: int) -> Image:
    """Resizes a given image."""
    background_color = (255, 255, 255, 0)
    image_mode = "RGBA"

    width, height = pil_image.size
    if width == height:
        return pil_image.resize((new_size, new_size), Image.LANCZOS)

    if width > height:
        result = Image.new(image_mode, (width, width), background_color)
        result.paste(pil_image, (0, (width - height) // 2))
        return result.resize((new_size, new_size), Image.LANCZOS)
    else:
        result = Image.new(image_mode, (height, height), background_color)
        result.paste(pil_image, ((height - width) // 2, 0))
        return result.resize((new_size, new_size), Image.LANCZOS)
