import setuptools
from gb2influxdb.version import version

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gb2influxdb",
    version=version,
    author="Travis Howse",
    author_email="tjhowse@gmail.com",
    description="A tool for syncing a Gadgetbridge database export to InfluxDB.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tjhowse/gb2influxdb",
    packages=setuptools.find_packages(),
    install_requires=[
        'click>=6.7',
    ],
    tests_require=[
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5.0',
    test_suite='nose2.collector.collector',
    entry_points='''
        [console_scripts]
        gb2influxdb=gb2influxdb.gb2influxdb:main
    ''',
)
