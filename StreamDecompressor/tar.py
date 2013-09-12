import tarfile as tarlib
import io

from . import Archive, ArchiveTemp


class Member(tarlib.ExFileObject, io.BufferedIOBase):
    def __init__(self, tarfile, tarinfo):
        self.wrapped = tarlib.ExFileObject(tarfile, tarinfo)
        io.BufferedIOBase.__init__(self)

    def readable(self):
        return True

    def read(self, n=-1):
        return self.wrapped.read(n if n > -1 else None)

class Untar(Archive):
    def __init__(self, name, fileobj):
        fileobj = ArchiveTemp(fileobj)
        self.tarfile = tarlib.TarFile.open(fileobj=fileobj)
        single = True
        stream = Member(self.tarfile, self.tarfile.next())
        if self.tarfile.next():
            single = False
            stream = None
        Archive.__init__(self, name, ['tar'], stream,
            source=fileobj, single=single)
