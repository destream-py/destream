from pathlib import Path
from setuptools import setup, find_packages

setup(
    name = "destream",
    version = "5.0.1",
    description = ("A simple module to decompress streams compressed multiple "
                   "times"),
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    license = "GPLv2",
    keywords = "stream file decompress zip zstd",
    url = "https://github.com/destream-py/destream",
    packages = find_packages(),
    scripts = ['scripts/destream'],
    install_requires = ['python-magic>=0.4.12'],
    extras_require={"test": ["tox", "pytest", "pytest-cov"]},
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Topic :: System :: Archiving :: Compression",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
