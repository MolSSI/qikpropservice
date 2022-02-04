from pathlib import Path
from shutil import rmtree, move
import traceback
from typing import Union

from werkzeug.datastructures import FileStorage

from app import celery
from ..qp import run_qikprop
from ..constants import QP_OUTPUT_TAR_NAME, INBOUND_PATH, SERVE_PATH


def _generate_dir_and_file_paths(directory, checksum, filename):
    target_dir = Path(directory, f"{checksum}").resolve()
    target_file = target_dir / filename  # Yay Path operations
    return target_dir, target_file


@celery.task()
def run_qikprop_worker(datafile: Union[Path, str], options: dict, checksum: str):
    datafile = Path(datafile)  # Cast to Path
    serve_directory, serve_file = _generate_dir_and_file_paths(SERVE_PATH, checksum, QP_OUTPUT_TAR_NAME)
    # Don't double up the work
    # Check does not work right now since tarballs are named QP_OUTPUT_TAR_NAME.{tarball hash}
    #     Leaving here until improvements can be made
    if serve_file.exists():
        return

    serve_directory.mkdir(parents=True, exist_ok=True)
    try:
        output_file = run_qikprop(datafile, datafile.name, options)
        output_file_path = Path(output_file)
        # Setup new location - Make the checksum directory

        # Move the file with shutil. Path.rename causes issues cross filesystem
        move(output_file_path, serve_file)
        # Cleanup inbound staging directory
        str_path = str(datafile)
        if str(INBOUND_PATH) in str_path and checksum in str_path:
            rmtree(datafile.parent)
    except Exception:
        e = serve_directory / "ErrorDetails.txt"
        with e.open("w") as f:
            f.write(traceback.format_exc())
    return


def inbound_staging(file: FileStorage, filename: str, checksum: str):
    """Setup inbound file staging. Do this because FileStorage isn't serializable in Celery"""
    inbound_directory, inbound_file = _generate_dir_and_file_paths(INBOUND_PATH, checksum, filename)
    # Don't overwrite staging files
    if inbound_file.exists():
        return inbound_file
    # Make the staging directory
    inbound_directory.mkdir(parents=True, exist_ok=True)
    # Save the file
    file.save(str(inbound_file))
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


def clear_output(checksum):
    """Delete any existing output given a specific checksum"""
    possible_tarball = serve_file(checksum)
    if isinstance(possible_tarball, Path):
        rmtree(possible_tarball.parent)
        return True
    return False

