import os
import errno
import io
import tempfile
from subprocess import Popen, PIPE
import threading


class Archive(io.BufferedReader):
    def __init__(self, name, compressions, fileobj=None, source=None):
        assert type(self) != Archive, \
            "This class can not be used in standalone"
        if not fileobj:
            fileobj = io.BytesIO()
        elif isinstance(fileobj, file):
            filename = fileobj.name
            fileobj = io.FileIO(fileobj.fileno(), closefd=False)
            fileobj.name = filename
        assert isinstance(fileobj, io.IOBase), \
            "fileobj must be an instance of io.IOBase or a file, got %s" \
            % type(fileobj)
        io.BufferedReader.__init__(self, fileobj)
        self.realname = name or ''
        self.source = source
        self.compressions = (source.compressions if isinstance(source, Archive)
            else []) + compressions


class ArchivePack(Archive):
    def __init__(self, name, compressions, fileobj=None, source=None):
        Archive.__init__(self, name, compressions, fileobj, source=source)

    def single(self):
        return len(self.members()) == 1

    def members(self):
        raise NotImplemented("class %s does not implement this method" \
            % type(self))

    def open(self, member):
        raise NotImplemented("class %s does not implement this method" \
            % type(self))

    def extract(self, member, path):
        raise NotImplemented("class %s does not implement this method" \
            % type(self))

    def extractall(self, path, members=None):
        raise NotImplemented("class %s does not implement this method" \
            % type(self))


class ArchiveFile(Archive):
    def __init__(self, fileobj=None, name=None):
        if not fileobj:
            if not name:
                raise TypeError("Either name, fileobj must be specified")
            fileobj = io.FileIO(name)
        elif not name and hasattr(fileobj, 'name'):
            name = fileobj.name
        Archive.__init__(self, name, [], fileobj, source=fileobj)


class ArchiveTemp(Archive):
    def __init__(self, fileobj, name=None):
        if isinstance(fileobj, Archive):
            if name is None: name = fileobj.realname
        else:
            name = fileobj.name
        tempdir = os.path.dirname(name)
        try:
            self.tempfile = tempfile.NamedTemporaryFile(dir=tempdir)
        except OSError:
            self.tempfile = tempfile.NamedTemporaryFile()
        self.tempfile.writelines(fileobj)
        self.tempfile.seek(0)
        fileio = io.FileIO(self.tempfile.fileno(), closefd=False)
        fileio.name = self.tempfile.name
        Archive.__init__(self, name, [], fileio, source=fileobj)


def make_seekable(fileobj):
    if isinstance(fileobj, file):
        filename = fileobj.name
        fileobj = io.FileIO(fileobj.fileno(), closefd=False)
        fileobj.name = filename
    assert isinstance(fileobj, io.IOBase), \
        "fileobj must be an instance of io.IOBase or a file, got %s" \
        % type(fileobj)
    return fileobj if fileobj.seekable() \
        else ArchiveTemp(fileobj)


class ExternalPipe(Archive, threading.Thread):
    def __init__(self, name, stdin):
        assert type(self) != ExternalPipe, \
            "This class can not be used in standalone"
        assert hasattr(self, '__command__'), \
            "__command__ attribute is missing in class %s" % type(self)
        assert hasattr(self, '__compressions__'), \
            "__compressions__ attribute is missing in class %s" % type(self)
        self.p = Popen(self.__command__, stdout=PIPE, stdin=PIPE)
        self.stdin = stdin
        threading.Thread.__init__(self)
        self.start()
        Archive.__init__(self, name, self.__compressions__,
            fileobj=self.p.stdout, source=stdin)

    def run(self):
        self.p.stdin.writelines(self.stdin)
        self.p.stdin.close()


from guesser import *
