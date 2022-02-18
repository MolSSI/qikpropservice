from flask import Blueprint

# Important flask note: Other Views such as an API have to be in a different directory from the normal "main" here
# Because otherwise the blueprint registration does not work due to how flask sorts out directory and import structure
# Its weird.

# This has to be here above the other imports to prevent circular import
main = Blueprint('main', __name__)

# This has to be below the declaration of main and api to prevent circular imports
# These imports are technically unused, but required to actually add all the routes
from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
