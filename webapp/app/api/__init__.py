from flask import Blueprint
from flask_restful import Api

api_blueprint = Blueprint("api", __name__)
api = Api(api_blueprint)

# This has to be below the declaration of main and api to prevent circular imports
# These imports are technically unused, but required to actually add all the routes
from . import api_views
