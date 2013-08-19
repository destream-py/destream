import tarfile
import io

from . import Archive


class Untar(Archive):
    def __init__(self, name, fileobj):
        self.tarfile = tarfile.TarFile(fileobj=fileobj)
        members = self.tarfile.getmembers()
        single = (len(members) == 1)
        stream = None
        if single:
            stream = io.BytesIO(self.tarfile.extractfile(members[0]).read())
        Archive.__init__(self, name, ['tar'], stream,
            source=fileobj, single=single)
