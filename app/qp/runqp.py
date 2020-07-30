import subprocess as sp
from tempfile import TemporaryDirectory
import os
import shutil
import pathlib
import contextlib
import tarfile
import hashlib
from abc import ABC, abstractmethod

hasher = hashlib

script_dir = pathlib.Path(__file__).parent.absolute()

default_qp_options = {
    "proc_mode": "normal",
    "nmol": 20
}


class Option(ABC):

    def __init__(self, *args):
        if not args:
            self._value = self.default
        else:
            self._value = args[0]

    @abstractmethod
    def map_value(self, val):
        pass

    @property
    @abstractmethod
    def option_name(self) -> str:
        pass

    @property
    @abstractmethod
    def default(self):
        pass

    @property
    def value(self):
        return self.map_value(self._value)

    @property
    def option(self):
        return {self.option_name, self.value}


class Fast(Option):

    @property
    def default(self):
        return "normal"

    @property
    def option_name(self) -> str:
        return "proc_mode"

    def map_value(self, val):
        if val:  # Maps True -> Fast
            return "fast"
        return "normal"


class Similar(Option):

    @property
    def default(self):
        return 20

    @property
    def option_name(self) -> str:
        return "nmol"

    def map_value(self, val):
        return int(val)


class OptionMap:
    methods = {
        "fast": Fast,
        "similar": Similar
    }

    def __init__(self, **kwargs):
        self._options = {}
        for known_option, known_map in self.methods.items():
            option_map = known_map()
            if known_option in kwargs:
                passed_value = kwargs[known_option]
                self._options[option_map.option_name] = option_map.map_value(passed_value)
            else:
                self._options[option_map.option_name] = option_map.default

    @classmethod
    def known_methods(cls):
        return [method for method in cls.methods.keys()]

    @classmethod
    def generate_options(cls, **kwargs):
        generator = cls(**kwargs)
        return generator.options

    @property
    def options(self):
        return self._options


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
    run_options = OptionMap.generate_options(**options)

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
