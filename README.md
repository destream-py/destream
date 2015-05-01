StreamDecompressor
==================

A simple module to decompress streams compressed multiple times

Synopsis
========

*   Open an archive that holds multiple files (aka: ArchivePack)
```python
archive = StreamDecompressor.open("some_file.tar.gz")

assert isinstance(archive, StreamDecompressor.ArchivePack) \
    and isinstance(archive.tarfile, tarfile.TarFile)

# ==> we can extract members using extract() and extractall()
archive.extractall("/tmp")
```
*   Open a compressed file (or stream) and get an uncompressed stream
```python
archive = StreamDecompressor.open("weird_file.bz2.gz")

assert isinstance(archive, StreamDecompressor.Archive)

# ==> we can read the content but not seek
print archive.read()
```
*   Open an archive that holds only one file,
```python
archive = StreamDecompressor.open("some_file.tar.xz")

# ==> we can read the archive like it is a stream
if archive.single():
    print archive.read()
else:
    archive.extractall('/tmp/some/path/')
```
