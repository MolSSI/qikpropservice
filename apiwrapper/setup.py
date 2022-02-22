from setuptools import setup, find_packages
import versioneer

short_description = "QikProp v3 As a Service API Wrapper Library and CLI tool."

try:
    with open("README.md", "r") as handle:
        long_description = handle.read()
except FileNotFoundError:
    long_description = short_description


if __name__ == "__main__":
    setup(
        name='qikpropservice',
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        description='API wrapper CLI and library for MolSSI QikProp as a Service',
        author='Levi Naden',
        author_email='lnaden@vt.edu',
        url="https://github.com/MolSSI/qikpropservice",
        license='MIT',

        packages=find_packages(),

        install_requires=["requests", "click", "pydantic", "tqdm"],

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
        entry_points={
            "console_scripts": [
                "qikpropcli = qikpropservice:qpcli"
            ]
        },
        long_description=long_description,
        long_description_content_type="text/markdown"
    )
