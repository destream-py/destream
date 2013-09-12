StreamDecompressor
==================

A simple module to decompress streams compressed multiple times

Synopsis
========

```python
import StreamDecompressor

import tarfile
archive = StreamDecompressor.open("some_file.tar.gz")
assert isinstance(archive, StreamDecompressor.ArchivePack) \
    and isinstance(archive.tarfile, tarfile.TarFile)

archive = StreamDecompressor.open("weird_file.lzma.gz")
assert isinstance(archive, StreamDecompressor.Archive)
print archive.read()

archive = StreamDecompressor.open("some_file.tar.xz")
# If the tar file contains only one member, this is possible
if archive.single():
    print archive.read()
else:
    archive.extractall('/tmp/some/path/')
```
