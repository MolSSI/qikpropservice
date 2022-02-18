import logging
from pathlib import Path
from typing import Tuple, Union

from flask import request, send_from_directory
from flask_restful import Resource, abort
from pydantic import ValidationError

from app.tasks import serve_file, response_code_from_tarball, generate_status, create_qikprop_task
from app.data_models import (StatusGET, GETPOSTError, ResultGET, StatusCodes, QikpropPOST, StatusGETReturn,
                             SeverHelloGETResponse)

from . import api


logger = logging.getLogger(__name__)

#  Logging to console in heroku
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def _check_args(input_model, model_args: dict, error_model=GETPOSTError):
    try:
        return input_model(**model_args)
    except ValidationError as e:
        return error_model(args=model_args, error=str(e))
    except:
        abort(520, message=f"Something went wrong during the argument parsing and caused the API to "
                           f"reach what should have been unreachable under normal circumstances. "
                           f"The expected model was {input_model} and args were {model_args}. "
                           f"Please report this to the site maintainers.")


def _compute_status(checksum: str) -> Tuple[Union[Path, str], int, StatusGETReturn]:
    """Parse the incoming hash to figure out if the job is present, running or not"""
    possible_tarball = serve_file(checksum)
    response_code = response_code_from_tarball(possible_tarball, checksum)
    status = generate_status(response_code, possible_tarball, checksum)
    return possible_tarball, response_code, status


class QikpropHelloWorld(Resource):
    def get(self):
        return SeverHelloGETResponse().dict(), 200


class QikpropStatus(Resource):
    def get(self):
        """Get the status of a QikProp Task"""
        # Get and parse the args from the request (Python requests(params=...) come through as Flask request.args
        args = _check_args(StatusGET, request.args)
        if isinstance(args, GETPOSTError):
            return args.dict(), args.code
        checksum = args.id
        _, response_code, status = _compute_status(checksum)
        return status.dict(), response_code


_tarbal_datatype = 'application/x-tar'


class QikpropData(Resource):
    def get(self):
        """Get the file, from a quikprop task"""
        # Get and parse the args from the request (Python requests(params=...) come through as Flask request.args
        args = _check_args(ResultGET, request.args)
        if isinstance(args, GETPOSTError):
            return args.dict(), args.code
        possible_tarball, response_code, status = _compute_status(args.id)
        if response_code != StatusCodes.ready:
            return status.dict(), response_code
        elif response_code == StatusCodes.ready:
            directory = str(possible_tarball.parent)
            filename = str(possible_tarball.name)
            response = send_from_directory(directory,
                                           filename,
                                           mimetype=_tarbal_datatype,  # Probably not needed
                                           filename=filename,
                                           as_attachment=True)
            response.status_code = response_code  # Adjust the status code for my own app
            return response
        else:  # Catch all for inappropriate requests that somehow made it here
            abort(520, message=f"Something went wrong during the file GET request and caused the API to "
                               f"reach what should have been unreachable under normal circumstances. "
                               f"The input code was {response_code}, the possible file was {possible_tarball}, "
                               f"and the headers were "
                               f"{request.headers}. "
                               f"Please report this to the site maintainers.")

    def post(self):
        """Add the file to the list if it's not there already"""
        args = _check_args(QikpropPOST, request.args)
        if isinstance(args, GETPOSTError):
            return args.dict(), args.code
        possible_tarball, response_code, status = _compute_status(args.id)
        if response_code != StatusCodes.null:  # Something is here
            return status.dict(), response_code  # Nothing to do here other than say its here
        return create_qikprop_task(request, args.dict(exclude={"id"}), args.id)


api.add_resource(QikpropHelloWorld, "/")
api.add_resource(QikpropStatus, "/status")
api.add_resource(QikpropData, "/tasks")
