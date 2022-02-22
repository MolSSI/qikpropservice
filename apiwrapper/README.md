[![codecov](https://codecov.io/gh/MolSSI/qikpropservice/branch/master/graph/badge.svg)](https://codecov.io/gh/MolSSI/qikpropservice)

MolSSI QikProp As A Service API Wrapper Library
===============================================

A library which wraps the API calls for the QikProp v3 As A Service 
 
The version of QikProp reached by this library has been provided by [William L. Jorgensen](http://zarbi.chem.yale.edu) 
and hosted as a service by the [Molecular Sciences Software Institute (MolSSI)](https://molssi.org/). To report a
problem or suggest improvements, please open an issue on
[the Project GitHub](https://github.com/MolSSI/qikpropservice). Additional features and options will be
added over time.

This project serves as the Python wrapper for making the API calls by providing both an importable 
library and a CLI tool to make calls to the QikProp Service.

For direct information regarding the API endpoints, please see 
[the Project GitHub](https://github.com/MolSSI/qikpropservice).

Installation From Conda or Pip
------------------------------

This package can be installed from either Conda (via Conda-Forge) or Pip

```bash
conda install -c conda-forge qikpropservice
```
OR
```bash
pip install qikpropservice
```

Installation from Source
------------------------

1. Clone the repo at https://github.com/MolSSI/qikpropservice
2. Navigate to the folder `apiwrapper`
3. Run `python setup.py install`

Usage as a CLI Tool
-------------------

The CLI can be run from any command line interface by invoking

```bash
qikpropcli
```

The CLI provides its own documentation for how to use it, but most commonly can be used as such:

```bash
qikpropcli run FILES
```
Where `FILES` can be replaced with any number of entries of files to submit to the QikProp Service API endpoints.
There are options which can be specified here such as custom URI server's (e.g. for local testing) or QikProp 
options, but all of those are documented in the `--help` flag.


Usage as a Python Library
-------------------------

There are two main library functions depending on if you want to do large bulk processing, or more fine-grained 
file-by-file processing. In either use case, the library works on on-disk files rather than data pre-read 
into memory.

The main helper function is `qikprop_as_a_service` which acts much as the CLI does in that it processes many files 
all the same way.

```python
from qikpropservice import qikprop_as_a_service

qikprop_as_a_service("file1.mol, file2.mol, ligand_series*.mol2")
```

This will run the two named files `file1.mol`, `file2.mol` and all the files matching the glob `ligand_series*.mol2`.
It is possible to set the output name of each of the returned `.tar.gz` files through a keyword. Other options such as 
what settings that can be passed to QikProp are available as well. See the function docstring or call 
`qikprop_as_a_service.__doc__` to see the options.

The second object is the API Endpoint call wrapper `QikpropAsAService` which can be used to 
integrate with exiting pipelines and make each of the API calls directly, without having to write the request itself 
directly. This class only works on a per-call/file basis. The `qikprop_as_a_service` function uses this class to make 
all of its calls and operations on each file. Its most common invocation is below (wrapped in a practical use), but 
things such as the URI, endpoints, hashing functions, etc. can all be set in the class initialization.

```python
from qikpropservice import QikpropAsAService, QikPropOptions
from time import sleep

service = QikpropAsAService() 

# Example of options, there are defaults for this model and it does not need to be passed to the Service calls 
# if only defaults are wanted 
options = QikPropOptions(fast=True, similar=30)

success, ret_code, data = service.post_task("file1.mol", options=options)
task_id = data["id"]
while True:
    success, ret_code, ret_data = service.get_result(task_id=task_id, output_file="file1_result.tar.gz")
    if success: 
        break
    sleep(5)
```

See the documentation for each class and function to see its options and expected returns.

Utility
-------
There is an expected return code dataclass called `StatusCodes`. It's a simple holder for information regarding the 
HTTP codes returned normally by the QikProp Service API Endpoint and what they mean.

The class is imported with
```python
from qikpropservice import StatusCodes

StatusCodes.ready      # 200
StatusCodes.created    # 201
StatusCodes.staged     # 202
StatusCodes.error      # 220
StatusCodes.null       # 404
StatusCodes.unmatched  # 409
```
where each of the attributes and codes corresponds to a particular meaning.

* ready : 200 - GET and POST
  - Task is ready to pull down.
* created: 201 - POST
  - Submitted task has been accepted by the server and no issues on input validation.
* staged: 202 - GET
  - Task is queued in the service but has not been processed or is in processing.
* error : 220 - GET
  - Task has been processed but had an error associated with processing. See data dict or pull error file for details.
* null : 404 - GET
  - No task exists on the server with a given ID
* unmatched : 409 - GET and POST
  - For a provided task ID and file data, Checksum/hashing does not match
