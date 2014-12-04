import zipfile
import io
import sys

from StreamDecompressor import ArchivePack, make_seekable, ArchiveFile

__all__ = ['Unzip']


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
        if self.single():
            self.__compression__ += ':' + self.members()[0].filename
        ArchivePack.__init__(self, name, source=fileobj,
            fileobj=(self.single() and self.open(self.members()[0])))

    def members(self):
        return self.zipfile.infolist()

    def open(self, member):
        return self.zipfile.open(member)

    def extract(self, member, path):
        return self.zipfile.extract(member, path)

    def extractall(self, path, members=None):
        return self.zipfile.extractall(path, members)
