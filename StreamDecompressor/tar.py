import tarfile
from io import BytesIO

from . import Archive


class Untar(BytesIO, Archive):
    def __init__(self, archive, filename):
        Archive.__init__(self, filename, archive.compressions + ['tar'])
        self.tarfile = tarfile.TarFile(fileobj=archive)
        members = self.tarfile.getmembers()
        if len(members) == 1:
            BytesIO.__init__(self, self.tarfile.extractfile(members[0]).read())
        else:
            BytesIO.__init__(self)
