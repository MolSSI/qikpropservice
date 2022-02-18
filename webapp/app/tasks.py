from pathlib import Path
from shutil import rmtree, move
from tempfile import TemporaryDirectory
import traceback
from typing import Union

from flask_restful import abort
from werkzeug.datastructures import FileStorage

from app.hashing import write_file_and_checksum_from_stream, hash_method
from app import celery
from app.constants import QP_OUTPUT_TAR_NAME, INBOUND_PATH, SERVE_PATH
from app.qp import run_qikprop
from app.data_models import StatusCodes, StatusGETReturn, GETPOSTError, QikpropPOSTResponse


def _generate_dir_and_file_paths(directory, checksum, filename):
    target_dir = Path(directory, f"{checksum}").resolve()
    target_file = target_dir / filename  # Yay, Path operations
    return target_dir, target_file


@celery.task()
def run_qikprop_worker(datafile: Union[Path, str], options: dict, checksum: str):
    datafile = Path(datafile)  # Cast to Path
    serve_directory, serve_file_path = _generate_dir_and_file_paths(SERVE_PATH, checksum, QP_OUTPUT_TAR_NAME)
    # Don't double up the work
    # Check does not work right now since tarballs are named QP_OUTPUT_TAR_NAME.{tarball hash}
    #     Leaving here until improvements can be made
    if serve_file_path.exists():
        return

    serve_directory.mkdir(parents=True, exist_ok=True)
    try:
        output_file = run_qikprop(datafile, datafile.name, options)
        output_file_path = Path(output_file)
        # Setup new location - Make the checksum directory

        # Move the file with shutil. Path.rename causes issues cross filesystem
        move(output_file_path, serve_file_path)
        # Cleanup inbound staging directory
        str_path = str(datafile)
        if str(INBOUND_PATH) in str_path and checksum in str_path:
            rmtree(datafile.parent)
    except Exception:
        e = serve_directory / "ErrorDetails.txt"
        with e.open("w") as f:
            f.write(traceback.format_exc())
    return


def prepare_inbound_staging(filename: str, checksum: str) -> Path:
    """Setup all of the directories and file locations """
    inbound_directory, inbound_file = _generate_dir_and_file_paths(INBOUND_PATH, checksum, filename)
    # Don't overwrite staging files
    if inbound_file.exists():
        return inbound_file
    # Make the staging directory
    inbound_directory.mkdir(parents=True, exist_ok=True)
    return inbound_file


def inbound_staging_web(file: FileStorage, filename: str, checksum: str):
    """Setup inbound file staging. Do this because FileStorage isn't serializable in Celery"""
    inbound_file = prepare_inbound_staging(filename, checksum)
    # Save the file
    file.save(str(inbound_file))
    return inbound_file


def inbound_staging_api(file: Path, filename: str, checksum: str):
    """Setup inbound file staging from some other location into a known location"""
    inbound_file = prepare_inbound_staging(filename, checksum)
    # Move the file with shutil. Path.rename causes issues cross filesystem
    move(file, inbound_file)
    return inbound_file


def serve_file(checksum):
    """See if the files are ready yet"""
    inbound_directory, _ = _generate_dir_and_file_paths(INBOUND_PATH, checksum, "junk.file")
    serve_directory, serve_file_path = _generate_dir_and_file_paths(SERVE_PATH, checksum, QP_OUTPUT_TAR_NAME)
    error_file = Path(serve_directory, "ErrorDetails.txt")
    # Serve tarball if there
    if serve_file_path.exists():
        return serve_file_path
    # serve the error file if there
    elif error_file.exists():
        return error_file
    # Serve info about file in staging
    elif inbound_directory.exists():
        return "In Staging"
    # Serve nothing
    return


def serialize_file_response(input_file: Path) -> Union[str, bytes]:
    serialized_file = ""
    return serialized_file


def deserialize_file_response(input_string: Path) -> str:  # Possibly not needed?
    deserialize_file = ""
    return deserialize_file


def consistent_file_response(file_string: Union[str, bytes]):
    """Helper function to ensure file response is consistent"""
    return {"file_data": file_string}


def package_file(possible_tarball, code):
    if code == StatusCodes.staged:
        return consistent_file_response("")
    return consistent_file_response(serialize_file_response(possible_tarball))


def generate_status(code: int, possible_tarball: Path, checksum: str) -> StatusGETReturn:
    ret = StatusGETReturn(id=checksum, code=code, message="")
    if code == StatusCodes.ready:
        ret.message = "Complete"
    elif code == StatusCodes.null:
        ret.message = f"No entry for {checksum}"  # File no found
    elif code == StatusCodes.staged:
        ret.message = "File is staged for processing or is being processed"
    elif code == StatusCodes.error:
        with open(possible_tarball, "r") as f:
            error = f.read()
        ret.message = "Complete, but threw error"
        ret.error = error
    else:
        # Something went wrong on the programing side here if this block is reached
        abort(520, message=f"The status of ID {checksum} was processed in a way to "
                           f"reach what should have been unreachable under normal circumstances. "
                           f"The valid codes were {list(StatusCodes.values)}. "
                           f"Actual code was {code}. Please report this to the site maintainers.")
    return ret


def response_code_from_tarball(possible_tarball: Union[str, Path, None], checksum: str):
    # No checksum found
    if possible_tarball is None:
        return StatusCodes.null
    # Checksum is present and done
    if isinstance(possible_tarball, Path):
        if QP_OUTPUT_TAR_NAME not in possible_tarball.name:
            return StatusCodes.error  # Case error file
        # Case valid/processed tarball
        return StatusCodes.ready

    # Checksum is still processing
    elif isinstance(possible_tarball, str):
        return StatusCodes.staged

    # Something went wrong on the programing side here if this block is reached
    abort(520, message=f"A possible file was requested under ID {checksum} which was processed in a way to "
                       f"reach what should have been unreachable under normal circumstances. The possible return "
                       f"tarball should have been a string, Path, or None. It was {type(possible_tarball)}. Please "
                       f"report this to the site maintainers.")


def clear_output(checksum):
    """Delete any existing output given a specific checksum"""
    possible_tarball = serve_file(checksum)
    if isinstance(possible_tarball, Path):
        rmtree(possible_tarball.parent)
        return True
    return False


def create_qikprop_task(request, options, checksum):
    # Check the checksum and the request match
    with TemporaryDirectory() as td:
        temp_file = Path(td) / "temp.data"
        # This will write and check the file
        computed_checksum = write_file_and_checksum_from_stream(request.stream, filepath=temp_file)
        if checksum != computed_checksum:
            return GETPOSTError(args=request.args,
                                error=f"ID of request did not match ID/checksum of file! "
                                      f"Input ID: {checksum}, Computed ID: {computed_checksum} "
                                      f"ID computation handled server side of file contents through "
                                      f"{hash_method.__name__}.",
                                code=StatusCodes.unmatched).dict(), StatusCodes.unmatched
        # TODO: Find a better file name, wont really matter here
        staged_file = inbound_staging_api(temp_file, "api_file.file", checksum)
    # Finally run the job
    run_qikprop_worker.delay(str(staged_file), options, checksum)
    print(options)
    return QikpropPOSTResponse(id=checksum, **options).dict(), StatusCodes.created





