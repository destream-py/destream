StreamDecompressor
==================

A simple module to decompress streams compressed multiple times

Example
=======

```python
import StreamDecompressor

import tarfile
archive = StreamDecompressor.open("some_file.tar.gz")
assert hasattr(archive, 'tarfile') \
    and isinstance(archive.tarfile, tarfile.TarFile)

archive = StreamDecompressor.open("weird_file.lzma.gz")
print archive.read()

archive = StreamDecompressor.open("some_file.tar.gz.lzma")
# If the tar file contains only one member, this is possible
print archive.read()
```
