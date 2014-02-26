import tarfile as tarlib
import io
from os import SEEK_SET

from StreamDecompressor import ArchivePack, make_seekable


class FileMember(io.IOBase, tarlib.ExFileObject):
    closed = None

    def __init__(self, tarfile, tarinfo):
        fileobj = tarfile.fileobj
        if isinstance(fileobj, file):
            fileobj = io.FileIO(tarfile.fileobj.fileno(), closefd=False)
        assert isinstance(fileobj, io.IOBase), \
            "fileobj must be an instance of io.IOBase or a file, got %s" \
            % type(fileobj)
        tarlib.ExFileObject.__init__(self, tarfile, tarinfo)
        self._readable = fileobj.readable()
        self._seekable = fileobj.seekable()

    def readable(self):
        return self._readable

    def seekable(self):
        return self._seekable

    def tell(self):
        return tarlib.ExFileObject.tell(self)

    def seek(self, offset, whence=SEEK_SET):
        tarlib.ExFileObject.seek(self, offset, whence)
        return self.tell()

    def read(self, n=-1):
        return tarlib.ExFileObject.read(self, (n if n > -1 else None))

    def readinto(self, b):
        if len(b) == 0: return None
        buf = self.read(len(b))
        b[:len(buf)] = buf
        return len(buf)


class Untar(ArchivePack):
    __mimes__ = ['application/tar']
    __extensions__ = ['tar']
    __compression__ = 'tar'

    def __init__(self, name, fileobj):
        fileobj = make_seekable(fileobj)
        self.tarfile = tarlib.TarFile.open(fileobj=fileobj)
        stream = FileMember(self.tarfile, self.tarfile.next())
        self._single = (self.tarfile.next() is None)
        if not self._single:
            stream = None
        ArchivePack.__init__(self, name, source=fileobj,
            fileobj=(self.single() and stream))

    def single(self):
        return self._single

    def members(self):
        return self.tarfile.getmembers()

    def open(self, member):
        return FileMember(self.tarfile, member)

    def extract(self, member, path):
        return self.tarfile.extract(member, path)

    def extractall(self, path, members=None):
        return self.tarfile.extractall(path, members)
