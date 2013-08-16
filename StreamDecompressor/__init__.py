import os
import errno
from io import IOBase, BufferedReader, BytesIO, FileIO
from subprocess import Popen, PIPE


class Archive(IOBase):
    def __init__(self, filename, compressions):
        self.realname = filename
        self.compressions = compressions


class ArchiveFile(BufferedReader, Archive):
    def __init__(self, filename=None, fileobj=None):
        assert filename or fileobj, \
            "One of these arguments must be specified: filename, fileobj"
        Archive.__init__(self, (filename if filename else fileobj.name), [])
        if not fileobj:
            BufferedReader.__init__(self, FileIO(filename))
        elif isinstance(fileobj, file):
            fileio = FileIO(fileobj.fileno(), closefd=False)
            fileio.name = fileobj.name
            BufferedReader.__init__(self, fileio)
        else:
            BufferedReader.__init__(self, fileobj)


class ExternalPipe(BytesIO):
    def __init__(self, command, fileobj, filename):
        p = Popen(command, stdout=PIPE, stdin=PIPE)
        p.stdin.writelines(fileobj)
        p.stdin.close()
        BytesIO.__init__(self, p.stdout.read())
        self.name = filename


from guesser import *
