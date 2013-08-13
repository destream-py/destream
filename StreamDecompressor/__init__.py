import os
import errno
from io import BufferedReader, BytesIO, FileIO, BufferedIOBase, DEFAULT_BUFFER_SIZE, SEEK_SET
from subprocess import Popen, PIPE


class Archive(object):
    def __init__(self, filename, compressions):
        self.realname = filename
        self.compressions = compressions


class ArchiveFile(BufferedReader, Archive):
    def __init__(self, filename=None, fileobj=None):
        assert filename or fileobj, \
            "One of these arguments must be specified: filename, fileobj"
        Archive.__init__(self, (filename if filename else fileobj.name), [])
        if fileobj:
            fileio = FileIO(fileobj.fileno(), closefd=False)
            fileio.name = fileobj.name
            BufferedReader.__init__(self, fileio)
        else:
            BufferedReader.__init__(self, FileIO(filename))


class ExternalPipe(BytesIO):
    def __init__(self, command, fileobj, filename):
        p = Popen(command, stdout=PIPE, stdin=PIPE)
        p.stdin.writelines(fileobj)
        p.stdin.close()
        BytesIO.__init__(self, p.stdout.read())
        self.name = filename


from guesser import *
