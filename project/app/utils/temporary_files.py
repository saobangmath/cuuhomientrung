import os
import re
import uuid
from django.conf import settings


UPLOADS_ROOT = getattr(settings, "UPLOADS_ROOT", None)
if UPLOADS_ROOT is None:
    raise Exception("UPLOADS_ROOT is not defined in settings.py")


def get_temp_file_path(ensure_dir=False):
    if (ensure_dir):
        os.makedirs(UPLOADS_ROOT, exist_ok=True)
    return os.path.join(UPLOADS_ROOT, str(uuid.uuid4()))


# For security reason, never use file path from user input.
# Use file name instead.
# File name must only contain alpha-numeric characters.

def path_to_name(path):
    return os.path.basename(path)


def name_to_path(name):
    if re.match(r'[A-Za-z0-9]+', name):
        return os.path.join(UPLOADS_ROOT, name)
    else:
        return None
