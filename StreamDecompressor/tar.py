from tarfile import TarFile
from io import BytesIO

from . import Archive

class Untar(BytesIO, Archive):
    def __init__(self, fileobj, filename):
        Archive.__init__(self, filename, fileobj.compressions + ['tar'])
        self.tarfile = TarFile(fileobj=fileobj)
        members = self.tarfile.getmembers()
        if len(members) == 1:
            BytesIO.__init__(self, self.tarfile.extractfile(members[0]).read())
        else:
            BytesIO.__init__(self, '')
