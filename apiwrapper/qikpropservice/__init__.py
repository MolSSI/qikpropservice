# CLI tool:
# Call files, parse options
# Hash files
# Check Against database for existing hash
# Send file and get signal
# Pull completed files


# The file data hashed in the webapp are also hashable through:
#   hashlib.sha1(f.read().encode('utf-8')).hexdigest()
# And yield the same result

from . import _version
__version__ = _version.get_versions()['version']

from .data_models import QikPropOptions, StatusCodes
from .qplib import qikprop_as_a_service, QikpropAsAService
from .qpcli import qpcli


