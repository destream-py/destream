import tarfile
from io import BytesIO

from . import Archive


class Untar(BytesIO, Archive):
    def __init__(self, archive, filename):
        self.tarfile = tarfile.TarFile(fileobj=archive)
        members = self.tarfile.getmembers()
        single = (len(members) == 1)
        Archive.__init__(self, filename,
            archive.compressions + ['tar'], single=single)
        if single:
            BytesIO.__init__(self, self.tarfile.extractfile(members[0]).read())
        else:
            BytesIO.__init__(self)
