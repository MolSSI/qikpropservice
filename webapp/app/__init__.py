import logging
import re

from .factory import make_celery, create_app
from . import _version

logger = logging.getLogger(__name__)

celery = make_celery()


__version__ = _version.get_versions()['version']
try:
    # Generate major/minor/patch from version string
    __version_spec__ = tuple(int(i) for i in re.search(r'(\d+)\.(\d+)\.(\d+)', __version__).groups())
    if len(__version_spec__) != 3:
        raise Exception
except:
    __version_spec__ = (0, 0, 0)
