[![Build Status](https://travis-ci.org/cecton/destream.svg?branch=master)](https://travis-ci.org/cecton/destream)
[![codecov](https://codecov.io/gh/cecton/destream/branch/master/graph/badge.svg)](https://codecov.io/gh/cecton/destream)

destream
========

_destream: decompress a stream_

Installation
------------

```pip install destream``` *OR* ```easy_install --user destream```

Usage
-----

1.  Decompress multiple files of anytype to directory:

    ```bash
    destream -o /tmp/output_dir file1.zip file2.rar file3.7z file4.tar.bz2
    ```
2.  Decompress any stream to the current folder:

    ```bash
    wget -O - "https://github.com/cecton/destream/archive/3.1.tar.gz" | destream -o ./
    ```
3.  Decompress any compressed file to stdout:

    ```bash
    destream documentation.gz | less
    ```



Lib Usage
---------

1.  Open an archive that holds multiple files (aka: ArchivePack)
    ```python
    archive = destream.open("some_file.tar.gz")

    assert isinstance(archive, destream.ArchivePack) \
        and isinstance(archive.tarfile, tarfile.TarFile)

    # ==> we can extract members using extract() and extractall()
    archive.extractall("/tmp")
    ```
2.  Open a compressed file (or stream) and get an uncompressed stream
    ```python
    archive = destream.open("weird_file.bz2.gz")

    assert isinstance(archive, destream.Archive)

    # ==> we can read the content but not seek
    print archive.read()
    ```
3.  Open an archive that holds only one file,
    ```python
    archive = destream.open("some_file.tar.xz")

    # ==> we can read the archive like it is a stream
    if archive.single():
        print archive.read()
    else:
        archive.extractall('/tmp/some/path/')
    ```

Troubleshooting
---------------

*   ```ImportError: failed to find libmagic.  Check your installation```

    *   Mac OS X: follow these
        [installation guide](http://www.brambraakman.com/blog/comments/installing_libmagic_in_mac_os_x_for_python-magic/). Or simply:

        ```
        brew install libmagic
        ```

    *   Arch Linux:

        ```
        pacman -S file
        ```
    *   Ubuntu/Debian:

        ```
        apt-get install libmagic1
        ```
