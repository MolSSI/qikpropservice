import setuptools
import pip
import sys


try:
    if pip.__version__ >= "19.3":
        from pip._internal.req import parse_requirements
        from pip._internal.network.session import PipSession
    elif pip.__version__ >= "10.0" and pip.__version__ < "19.3":
        from pip._internal.req import parse_requirements
        from pip._internal.download import PipSession
    else:  # pip < 10 is not supported
        raise Exception('Please upgrade pip: pip install --upgrade pip')
except ImportError as err: # for future changes in pip
    print('New breaking changes in pip!!', err)
    sys.exit()


def read_requirements():
    """parses requirements from requirements.txt"""

    install_reqs = parse_requirements('requirements.txt', session=PipSession())
    return [ir.name for ir in install_reqs]


def read_requirements():
    """parses requirements from requirements.txt"""

    install_reqs = parse_requirements('requirements.txt', session=PipSession())
    return [ir.name for ir in install_reqs]


if __name__ == "__main__":
    setuptools.setup(
        name='COVID_APIS',
        version="0.1.0",
        description='REST APIS for MolSSI COVID19 project',
        author='Doaa Altarawy',
        author_email='doaa.altarawy@gmail.com',
        url="https://github.com/MolSSI/covid_apis",
        license='BSD-3C',

        packages=setuptools.find_packages(),

        install_requires=read_requirements(),

        include_package_data=True,

        extras_require={
            'tests': [
                "pytest",
                "pytest-cov",
            ],
        },

        tests_require=["pytest", "pytest-cov"],

        classifiers=[
            'Development Status :: 4 - Beta',
            'Intended Audience :: Science/Research',
            'Programming Language :: Python :: 3',
        ],
        zip_safe=True,
    )
