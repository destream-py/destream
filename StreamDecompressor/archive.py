import re
import os
import sys
import errno
import io
import tempfile
from subprocess import Popen, PIPE
import threading
from distutils.spawn import find_executable

if sys.version_info < (2, 7):
    io_name_attr = '_name'
else:
    io_name_attr = 'name'

__all__ = """\
        Archive ArchivePack ArchiveFile ArchiveTemp ExternalPipe
        make_seekable
    """.split()


re_extension = re.compile('^(.*?)(\.([^.]+))?$')

class Archive(io.BufferedReader):
    """
    Base class to Archive file
    """
    def __init__(self, name, fileobj=None, source=None):
        assert type(self) != Archive, \
            "This class can not be used in standalone"
        if not fileobj:
            fileobj = io.BytesIO()
        elif isinstance(fileobj, file):
            filename = fileobj.name
            fileobj = io.FileIO(fileobj.fileno(), closefd=False)
            setattr(fileobj, io_name_attr, filename)
        assert isinstance(fileobj, io.IOBase), \
            "fileobj must be an instance of io.IOBase or a file, got %s" \
            % type(fileobj)
        io.BufferedReader.__init__(self, fileobj)
        # TODO: not sure if it is the best things to do...
        if sys.version_info < (2, 6, 5) and not hasattr(self, 'name'):
            self.name = getattr(fileobj, 'name', name)
        self.realname = name or ''
        self.source = source
        if isinstance(source, Archive):
            self.__decompressors__ = source.__decompressors__ + [type(self)]
            self.compressions = list(source.compressions)
        else:
            self.__decompressors__ = [type(self)]
            self.compressions = []
        if hasattr(self, '__compression__'):
            self.compressions += [self.__compression__]

    @classmethod
    def __checkavailability__(self):
        pass

    @classmethod
    def __guess__(cls, mime, name, fileobj):
        match = re_extension.search(name)
        if mime in cls.__mimes__:
            return match.group(1)
        if match.group(2) and match.group(3) in cls.__extensions__:
            return match.group(1)
        raise ValueError(
            (cls, mime, name, fileobj),
            "can not decompress fileobj using cls")


class ArchivePack(Archive):
    """
    Base class for an archive that is also a pack of file (tar, zip, ...)
    """
    def __init__(self, name, fileobj=None, source=None):
        Archive.__init__(self, name, fileobj, source=source)

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
    """
    Make an archive from a file-object
    """
    def __init__(self, fileobj=None, name=None):
        if not fileobj:
            if not name:
                raise TypeError("Either name, fileobj must be specified")
            fileobj = io.FileIO(name)
        elif not name and hasattr(fileobj, 'name'):
            name = fileobj.name
        Archive.__init__(self, name, fileobj, source=fileobj)


class ArchiveTemp(Archive):
    """
    Write down a file-object to a temporary file and make an archive from it
    """
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
        setattr(fileio, io_name_attr, self.tempfile.name)
        Archive.__init__(self, name, fileio, source=fileobj)


def make_seekable(fileobj):
    """
    If the file-object is not seekable, return  ArchiveTemp of the fileobject,
    otherwise return the file-object itself
    """
    if isinstance(fileobj, file):
        filename = fileobj.name
        fileobj = io.FileIO(fileobj.fileno(), closefd=False)
        setattr(fileobj, io_name_attr, filename)
    assert isinstance(fileobj, io.IOBase), \
        "fileobj must be an instance of io.IOBase or a file, got %s" \
        % type(fileobj)
    return fileobj if fileobj.seekable() \
        else ArchiveTemp(fileobj)


class ExternalPipe(Archive, threading.Thread):
    """
    Pipe a file-object to a command and make an archive of the output
    """
    def __init__(self, name, stdin):
        assert type(self) is not ExternalPipe, \
            "This class can not be used in standalone"
        assert hasattr(self, '__command__'), \
            "__command__ attribute is missing in class %s" % type(self)
        self.p = Popen(self.__command__, stdout=PIPE, stdin=PIPE)
        self.stdin = stdin
        threading.Thread.__init__(self)
        self.start()
        Archive.__init__(self, name, fileobj=self.p.stdout, source=stdin)

    @classmethod
    def __checkavailability__(cls):
        assert cls is not ExternalPipe, \
            "This class can not be used in standalone"
        assert hasattr(cls, '__command__'), \
            "__command__ attribute is missing in class %s" % cls
        if find_executable(cls.__command__[0]) is None:
            raise OSError(2, cls.__command__[0], "cannot find executable")

    def run(self):
        self.p.stdin.writelines(self.stdin)
        self.p.stdin.close()
