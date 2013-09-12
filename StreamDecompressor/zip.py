import zipfile
import io

from . import Archive, ArchiveTemp


class Unzip(Archive):
    def __init__(self, name, fileobj):
        # part of the Zip header is at the end of the file. Therefore, we have
        # to create a temporary file from the previous stream and write the
        # whole content
        fileobj = ArchiveTemp(fileobj)
        self.zipfile = zipfile.ZipFile(fileobj)
        members = self.zipfile.infolist()
        single = (len(members) == 1)
        Archive.__init__(self, name, ['zip'],
            self.zipfile.open(members[0]),
            source=fileobj, single=single)
