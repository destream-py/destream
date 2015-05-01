Python's destream
=================

_destream: decompress a stream_

Synopsis
--------

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
