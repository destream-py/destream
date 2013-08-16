import py7zlib
from io import BytesIO

from . import Archive, ExternalPipe

__all__ = ['Un7z']


class Un7z(BytesIO, Archive):
    def __init__(self, archive, filename):
        Archive.__init__(self, filename, archive.compressions + ['7z'])
        self.p7zfile = py7zlib.Archive7z(archive)
        # Workaround for pylzma issue #14
        if self.p7zfile.numfiles == 1 or \
           not hasattr(self.p7zfile.files[0], 'filename'):
            BytesIO.__init__(self, self.p7zfile.files[0].read())
        else:
            BytesIO.__init__(self)
