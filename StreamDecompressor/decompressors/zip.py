import zipfile
import io
import sys

from StreamDecompressor import ArchivePack, make_seekable, ArchiveFile

if sys.version_info < (2, 7):
    # Make member file-like object inheriting from io.BufferedIOBase
    # (just like Python-2.7)
    class ZipExtFile(io.BufferedIOBase):
        closed = None

        def __init__(self, fileobj):
            self.fileobj = fileobj
            for symbol in ('read', 'readline', 'readlines'):
                setattr(self, symbol, getattr(fileobj, symbol))

        def readable(self):
            return True

        def seekable(self):
            return False

        def readinto(self, b):
            if len(b) == 0: return None
            buf = self.read(len(b))
            b[:len(buf)] = buf
            return len(buf)


class Unzip(ArchivePack):
    __mimes__ = ['application/zip']
    __extensions__ = ['zip']
    __compression__ = 'zip'

    def __init__(self, name, fileobj):
        # part of the Zip header is at the end of the file. Therefore, we have
        # to create a temporary file from the previous stream and write the
        # whole content
        fileobj = make_seekable(fileobj)
        self.zipfile = zipfile.ZipFile(fileobj)
        ArchivePack.__init__(self, name, source=fileobj,
            fileobj=(self.single() and self.open(self.members()[0])))

    def members(self):
        return self.zipfile.infolist()

    def open(self, member):
        if sys.version_info < (2, 7):
            return ZipExtFile(self.zipfile.open(member))
        else:
            return self.zipfile.open(member)

    def extract(self, member, path):
        return self.zipfile.extract(member, path)

    def extractall(self, path, members=None):
        return self.zipfile.extractall(path, members)
