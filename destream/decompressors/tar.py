import tarfile as tarlib
import io
import sys
from os import SEEK_SET

from destream import ArchivePack, make_seekable

__all__ = ['Untar']


class FileMember(io.IOBase, tarlib.ExFileObject):
    closed = None

    def __init__(self, tarfile, tarinfo):
        tarlib.ExFileObject.__init__(self, tarfile, tarinfo)
        self._readable = tarfile.fileobj.readable()
        self._seekable = tarfile.fileobj.seekable()

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

    def close(self):
        self.fileobj.fileobj.close()
        self.closed = True

    # This code is not from scratch but based on tarfile read() method
    def peek(self, n):
        buf = ""
        if self.buffer:
            buf = self.buffer[:n]
            self.buffer = self.buffer[n:]
        n = min(n, self.fileobj.size - self.fileobj.position)
        pos = self.fileobj.fileobj.tell()
        self.fileobj.fileobj.seek(self.fileobj.offset + self.fileobj.position)
        buf += self.fileobj.fileobj.peek(n - len(buf))
        self.fileobj.fileobj.seek(pos)
        return buf

    def readinto(self, b):
        if len(b) == 0: return None
        buf = self.read(len(b))
        b[:len(buf)] = buf
        return len(buf)


class Untar(ArchivePack):
    _mimes = ['application/x-tar']
    _extensions = ['tar']
    __compression = 'tar'
    _compression = 'tar'

    def __init__(self, name, fileobj):
        source = make_seekable(fileobj)
        self.tarfile = tarlib.TarFile.open(fileobj=source)
        first_member = self.tarfile.next()
        if first_member is None:
            raise IOError("can not read first member of the tar archive")
        self._single = (self.tarfile.next() is None)
        if self._single:
            if sys.version_info < (3, 0):
                stream = FileMember(self.tarfile, first_member)
            else:
                stream = tarlib.ExFileObject(self.tarfile, first_member)
            stream_name = first_member.name
            self._compression += ':' + stream_name
        else:
            stream_name = name
            stream = source
            stream.seek(0)
        ArchivePack.__init__(self, stream_name, source=source, fileobj=stream)

    def single(self):
        return self._single

    def members(self):
        pos = self.source.tell()
        members = self.tarfile.getmembers()
        self.source.seek(pos)
        return members

    def open(self, member):
        if sys.version_info < (3, 0):
            return FileMember(self.tarfile, member)
        else:
            return tarlib.ExFileObject(self.tarfile, member)

    def extract(self, member, path):
        return self.tarfile.extract(member, path)

    def extractall(self, path, members=None):
        return self.tarfile.extractall(path, members)

    def close(self):
        return super(Untar, self).close() if self.single() \
            else self.tarfile.close()

    @property
    def closed(self):
        return super(Untar, self).closed if self.single() \
            else self.tarfile.closed
