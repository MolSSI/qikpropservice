import subprocess as sp
from tempfile import TemporaryDirectory
import os
import shutil
import pathlib
import contextlib
import tarfile
import hashlib

hasher = hashlib

script_dir = pathlib.Path(__file__).parent.absolute()

default_qp_options = {
    "proc_mode": "normal",
    "nmol": 20
}


@contextlib.contextmanager
def temp_set_environ(variable, value):
    existing = os.environ.get(variable, None)
    os.environ[variable] = value
    yield
    if existing is None:
        del os.environ[variable]
    else:
        os.environ[variable] = existing


@contextlib.contextmanager
def temp_cd(*args, **kwargs):
    pwd = pathlib.Path().absolute()
    with TemporaryDirectory(*args, **kwargs) as tmp_dir:
        os.chdir(tmp_dir)
        yield
    os.chdir(pwd)


def run_qikprop(data, filename, options):
    # Find the qikprop dir
    qp_dir = os.path.join(script_dir, 'QikProp')
    # Parse the options
    run_options = {}
    for option, default_value in default_qp_options.items():
        if option in options:
            run_options[option] = options[option]
        else:
            run_options[option] = default_value

    # Create the temporary space
    with temp_set_environ("QPdir", qp_dir):
        with temp_cd():
            # Write the data file
            with open(filename, 'wb') as data_file:
                data_file.write(data.stream.read())
            # Copy the existing QPlimits and apply settings
            with open(os.path.join(qp_dir, 'QPlimits_mod'), 'r') as limits_skel:
                limits = limits_skel.read()
            with open('QPlimits', 'w') as limits_output:
                limits_output.write(limits.format(**run_options))
            # Run qikprop
            xqp = os.path.join(qp_dir, 'xQPROP')
            qp_commands = [xqp, filename]
            proc = sp.run(qp_commands, stdout=sp.PIPE, stderr=sp.PIPE)
            # Write outputs
            with open('stdout', 'w') as stdout:
                stdout.write(proc.stdout.decode())
            with open('stder', 'w') as stderr:
                stderr.write(proc.stderr.decode())
            # Make a tarball of the outputs
            tarball_name = "qp_data.tar.gz"
            with tarfile.open(tarball_name, mode="w:gz") as tarball:
                for out_data in ["QPSA.out", "QP.out", "QP.CSV", "QPwarning", "QPlog", "stderr", "stdout"]:
                    try:
                        tarball.add(out_data)
                    except:
                        # Not really caring if the data aren't there
                        pass
                tar_hash = str(hash(tarball))[:8]
            # Copy to the staging directory, add a bit of hash data to avoid overwrite
            stage_name = tarball_name + '.' + tar_hash
            stage_path = os.path.join(script_dir, "staging", stage_name)
            shutil.copyfile(tarball_name, os.path.join(script_dir, "staging", stage_name))
    return stage_path
