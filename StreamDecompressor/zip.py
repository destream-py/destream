import zipfile
import io

from . import Archive


class Unzip(Archive):
    def __init__(self, name, fileobj):
        self.zipfile = zipfile.ZipFile(fileobj)
        members = self.zipfile.infolist()
        single = (len(members) == 1)
        stream = io.BytesIO()
        if single:
            stream.writelines(self.zipfile.open(members[0]))
            stream.seek(0)
        Archive.__init__(self, name, ['zip'], stream,
            source=fileobj, single=single)
