from setuptools import setup, find_packages

setup(
    name = "destream",
    version = "5.0.1",
    author = "Cecile Tonglet",
    author_email = "cecile.tonglet@cecton.com",
    description = ("A simple module to decompress streams compressed multiple "
                   "times"),
    license = "GPLv2",
    keywords = "stream file decompress zip zstd",
    url = "https://github.com/cecton/destream",
    packages = find_packages(),
    scripts = ['scripts/destream'],
    install_requires = ['python-magic>=0.4.12'],
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Topic :: System :: Archiving :: Compression",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
)
