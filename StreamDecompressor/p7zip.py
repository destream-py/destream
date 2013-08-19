import py7zlib
from io import BytesIO

from . import Archive

__all__ = ['Un7z']


class Un7z(Archive):
    def __init__(self, name, fileobj):
        self.p7zfile = py7zlib.Archive7z(fileobj)
        # no filename attribute is a workaround for pylzma issue #14
        single = (self.p7zfile.numfiles == 1 or \
                  not hasattr(self.p7zfile.files[0], 'filename'))
        Archive.__init__(self, name, ['7z'],
            BytesIO(self.p7zfile.files[0].read() if single else ''),
            source=fileobj, single=single)
