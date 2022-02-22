"""
QikProp API Wrapper Library

Provides all the functions which can be called from the CLI or as a library
"""

from contextlib import contextmanager
from pathlib import Path
from time import sleep
from typing import List, Optional, Union

from tqdm import tqdm
import requests

from .data_models import StatusCodes, StatusGETReturn, QikPropOptions, SeverHelloGETResponse
from .hashing import generate_checksum_file, DEFAULT_HASH_FUNCTION


class _UpdateProgressBar:
    def __init__(self, enabled=False, size_in_bytes=0):
        self.enabled = enabled
        self.size_in_bytes = size_in_bytes
        self.progress_bar = None
        if enabled:
            self.progress_bar = tqdm(total=self.size_in_bytes, unit='iB', unit_scale=True)

    def update(self, length):
        if self.enabled:
            self.progress_bar.update(length)

    def close(self):
        if self.enabled:
            self.progress_bar.close()

@contextmanager
def _handle_progress_bar(size, enable=False):
    progress_bar = _UpdateProgressBar(enabled=enable, size_in_bytes=size)
    yield progress_bar
    progress_bar.close()


class QikpropAsAService:
    """
    QikProp As A Service API Endpoint wrapper.

    A class which wraps, calls, and handles the outputs from the
    """

    def __init__(self,
                 server="http://qikprop.molssi.org/api/v1",
                 status_endpoint="/status",
                 task_endpoint="/tasks",
                 hash_function=DEFAULT_HASH_FUNCTION,
                 blocksize=1024
                 ):
        self.server = server
        self.status_endpoint = status_endpoint
        self.task_endpoint = task_endpoint
        self.hash_function = hash_function
        self.blocksize = blocksize

    def _check_class_id(self, task_id: str = None, filepath: Union[Path, str] = None):
        if not (task_id or filepath):
            raise ValueError("Need either task_id or filepath")
        if filepath:
            checksum = generate_checksum_file(filepath, hash_function=self.hash_function)
            if task_id and checksum != task_id:
                raise ValueError(f"Provided Task ID was {task_id}, but provided filepath of {filepath} generated a "
                                 f"task ID of {checksum}. These should be the same if both are provided")
            task_id = checksum
        return task_id

    def server_status(self):
        """
        Check if the server responds

        Raises
        -------
        requests.exceptions.HTTPError
            If the server does not respond, raises the HTTP error.
        """
        r = requests.get(self.server)
        r.raise_for_status()
        response = SeverHelloGETResponse(**r.json())
        return True, response.dict()

    def get_status(self, *, task_id: str = None, filepath: Union[Path, str] = None):
        """
        Check the status of a task on the server

        Parameters
        ----------
        task_id : str
            Task ID to query against the server. Either this or filepath is required
            If task_id does not match the checksum/ID computed from the filepath contents, an error is raised
        filepath : Path or str
            Path to the file compute a checksum to generate a task_id. Either this or task_id is required
            If checksum/ID computed from the filepath contents does not match a provided task_id, an error is raised

        Returns
        -------
        success : bool
            If the request was accepted and processed normally. This should always return True if the server is reached
        code : int
            HTTP return code. See the StatusCodes class for expected codes
        data : dict
            Additional data and parameters with the post. "id" key has the task ID

        Raises
        ------
        ValueError
            If a return code is retrieved where the server returns a code not in StatusCodes, then something unexpected
            on the handoff has happened and this should be reported to the developers. 7

        """
        task_id = self._check_class_id(task_id=task_id, filepath=filepath)
        uri = self.server + self.status_endpoint
        r = requests.get(uri, params={"id": task_id})
        if r.status_code in StatusCodes.values:
            return True, r.status_code, StatusGETReturn(**r.json())
        # Something has gone wrong if we got here
        raise ValueError(f"Unexpected return code of {r.status_code} and message\n\n{r.text}")

    def get_result(self,
                   *,
                   task_id: str = None,
                   filepath: Union[Path, str] = None,
                   output_file: Union[Path, str] = Path("result.tar.gz"),
                   use_progress_bar: bool = False,
                   blocksize: Optional[int] = None
                   ):
        """
        Get a processed file (if ready) from the server

        Parameters
        ----------
        task_id : str
            Task ID to query against the server. Either this or filepath is required
            If task_id does not match the checksum/ID computed from the filepath contents, an error is raised
        filepath : Path or str
            Path to the file compute a checksum to generate a task_id. Either this or task_id is required
            If checksum/ID computed from the filepath contents does not match a provided task_id, an error is raised
        output_file : Path or str, Default: "result.tar.gz"
            Name of the tarfile to save when getting data from the server
            If there is a processing error reported by the server, a .err will be added to the suffix
        use_progress_bar : bool, Default: False
            Display a download progress bar. In most cases the QikProp output is very small O(10 kB) so the progress
            bar will resolve faster than it can provide useful data.
        blocksize : int, Optional
            Size of the download blocks to fetch from the request. Useful for breaking up large expected returns so
            data can be streamed to file rather than held in memory. If not set, uses the value set at class
            instantiation.

        Returns
        -------
        success : bool
            If the request was accepted and processed normally
        code : int
            HTTP return code. See the StatusCodes class for expected codes
        data : dict
            Additional data and parameters with the post. "id" key has the task ID

        Raises
        ------
        ValueError
            When the server responds with a particular code indicating that something unexpected happened on the server,
            but it was something which can be debugged through a catch all the server is coded to handle. If you get
            this, you should report it to the developers.
        """
        blocksize = blocksize if blocksize is not None else self.blocksize
        task_id = self._check_class_id(task_id=task_id, filepath=filepath)
        output_file = Path(output_file)  # Ensure Path object
        uri = self.server + self.task_endpoint
        r = requests.get(uri, params={"id": task_id}, stream=True)
        code = r.status_code
        if code == StatusCodes.ready:
            total_size_in_bytes = int(r.headers.get('content-length', 0))
            with _handle_progress_bar(total_size_in_bytes, enable=use_progress_bar) as progress_bar:
                with output_file.open(mode="wb") as output:
                    for data in r.iter_content(blocksize):
                        progress_bar.update(len(data))
                        output.write(data)
            return True, code, {}
        elif code >= 500:
            raise ValueError(f"Something went wrong on the request, but the server detected something unexpected "
                             f"happened in a way it can provide feedback that can be given to the developers. "
                             f"See below for details.\n\n"
                             f"Code {r.status_code}: {r.json()['message']}")
        return False, code, r.json()

    def post_task(self,
                  filepath: Union[Path, str],
                  *,
                  options: Union[dict, QikPropOptions] = QikPropOptions()
                  ):
        """
        Post a file to the server for processing

        Parameters
        ----------
        filepath : Path or str
            Path to the file to upload to the server
        options : QikPropOptions or dict matching spec
            Additional options to pass to QikProp, matches the QikPropOptions spec

        Returns
        -------
        success : bool
            If the request was accepted and processed normally
        code : int
            HTTP return code. See the StatusCodes class for expected codes
        data : dict
            Additional data and parameters with the post. "id" key has the task ID

        Raises
        ------
        ValueError
            When the server responds with a particular code indicating that something unexpected happened on the server,
            but it was something which can be debugged through a catch all the server is coded to handle. If you get
            this, you should report it to the developers.
        """
        filepath = Path(filepath)  # Ensure Path object
        checksum = self._check_class_id(filepath=filepath)
        if isinstance(options, dict):
            options = QikPropOptions(**options)
        uri = self.server + self.task_endpoint
        params = {"id": checksum, **options.dict()}
        with filepath.open("rb") as upload_file:
            r = requests.post(uri, data=upload_file, params=params, stream=True)
        code = r.status_code
        data = r.json()
        if code <= 300:
            return True, code, data
        elif code >= 500:
            raise ValueError(f"Something went wrong on the request, but the server detected something unexpected "
                             f"happened in a way it can provide feedback that can be given to the developers. "
                             f"See below for details.\n\n"
                             f"Code {r.status_code}: {r.json()['message']}")
        return False, code, data


def qikprop_as_a_service(filepaths: Union[str, Path, List[Union[str, Path]]],
                         *,  # kwonly args here
                         output_tar_names=None,
                         fast: bool = False,
                         similar: int = 20,
                         server_uri: str = "https://qikprop.molssi.org/api",
                         non_exist_ok: bool = False
                         ):
    """
    Run QikProp as a Service over a series of files and generate their results. This is more meant as a helper function.
    If you want to run QikProp on a per-file basis with much more fine-grained control over the options, you can use
    the QikpropAsAService class and methods.

    Parameters
    ----------
    filepaths: str, Path, List of str/Path
        Filepath(s) to be analyzed by QikProp
    output_tar_names: str, Path, List of str/Path equal in size to filepaths, optional
        Output file names from the qikprop service. If not set, output files will
        "{file name without extension}.qpout.tar.gz"
    fast: bool, Default = False
        QikProp Option, Fast processing mode
    similar: int, Default = 20
        QikProp Option, Number of similar molecules to return
    server_uri: str, Default = "https://qikprop.molssi.org/api"
        API endpoint URI
    non_exist_ok: bool, Default = False
        Check if all input files exist or not, if not, an error will be raised
    """
    input_files = []
    output_files = []
    problem_paths = []
    # Process single input
    if isinstance(filepaths, str) or isinstance(filepaths, Path):
        filepaths = [filepaths]
    # De-glob all inputs
    for single_path in filepaths:
        input_files.extend(Path().glob(str(single_path)))
    # Pre-process outputs
    if output_tar_names is not None and len(output_tar_names) != len(input_files):
        raise ValueError(f"Length of output_tar_names does not equal length of globed input files:\n"
                         f"Input files: {str(input_file for input_file in input_files)}\n"
                         f"Output Files: {str(output_tar_name for output_tar_name in output_tar_names)}")
    # Check files exist and prep output files
    for index, input_file in enumerate(input_files):
        if not input_file.exists() and not non_exist_ok:
            problem_paths.append(input_file)
        if output_tar_names is not None:
            output_files.append(output_tar_names[index])
        else:
            tarball_name = input_file.stem + ".qpout.tar.gz"
            output_files.append(input_file.parent / Path(tarball_name))

    # Initialize QikProp Service
    options = QikPropOptions(fast=fast, similar=similar)
    qps = QikpropAsAService(server=server_uri)
    task_ids = []
    task_output_map = {}
    errors = []
    # Upload all tasks
    for filepath, output_path in zip(input_files, output_files):
        success, code, data = qps.post_task(filepath,
                                            options=options)
        if success:
            task_ids.append(data["id"])
            task_output_map[data["id"]] = output_path
        else:
            errors.append((filepath, data))
    task_ids = set(task_ids)
    # Process all tasks
    progress = tqdm(total=len(task_ids))
    maximum_waits = 100
    waits = tqdm(total=maximum_waits, position=1, unit="waits")
    counter = 0
    while True:
        tasks_to_remove = []
        check_codes = []
        for task_id in task_ids:
            _, check_code, task_status = qps.get_status(task_id=task_id)
            check_codes.append(check_code)
            # get file
            if check_code in [StatusCodes.ready, StatusCodes.error]:
                output = task_output_map[task_id]
                downloaded, get_code, data = qps.get_result(task_id=task_id,
                                                            output_file=output,
                                                            use_progress_bar=False
                                                            )
                progress.update(1)
                if not downloaded:
                    with open(output.with_suffix(output.suffix + ".err"), "w") as errfile:
                        errfile.write(str(data))
                tasks_to_remove.append(task_id)
        for task_id in tasks_to_remove:
            task_ids.remove(task_id)

        counter += 1
        waits.update(1)
        if counter >= maximum_waits or len(task_ids) == 0:
            break
        sleep(5)



