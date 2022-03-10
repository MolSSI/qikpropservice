[![codecov](https://codecov.io/gh/MolSSI/qikpropservice/branch/master/graph/badge.svg)](https://codecov.io/gh/MolSSI/qikpropservice)

MolSSI QikProp As A Service
===========================

A repository for serving QikProp v3 as a webservice and API access point.
 
This version of QikProp has been provided by [William L. Jorgensen](http://zarbi.chem.yale.edu) and hosted as
a service by the [Molecular Sciences Software Institute (MolSSI)](https://molssi.org/). To report a
problem or suggest improvements, please open an issue on
[the Project GitHub](https://github.com/MolSSI/qikpropservice). Additional features and options will be
added over time.

There are two main components for this project:
* A web application where data can be uploaded in the form, and provides the endpoint for the API
* A standalone API wrapper for CLI calls to the service hosted through the web app

Please visit each subproject's folder and to see the documentation for each one.

Webapp Front End
----------------
The web application and service can be found at https://qikprop.molssi.org. 

CLI and Python Library
----------------------
The CLI tool and Python Library are downloadable through PyPI or Conda-Forge 

```bash
conda install -c conda-forge qikpropservice
```
OR
```bash
pip install qikpropservice
```
