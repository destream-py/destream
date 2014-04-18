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
    def __init__(self, name, fileobj=None, source=None, closefd=True):
        assert type(self) != Archive, \
            "This class can not be used in standalone"
        if not fileobj:
            fileobj = io.BytesIO()
        elif isinstance(fileobj, file):
            filename = fileobj.name
            fileobj = io.FileIO(fileobj.fileno(), closefd=False)
            setattr(fileobj, io_name_attr, filename)
        elif isinstance(fileobj, int):
            fileobj = io.FileIO(fileobj, closefd=False)
            setattr(fileobj, io_name_attr, name)
        assert isinstance(fileobj, io.IOBase), \
            "fileobj must be an instance of io.IOBase or a file, got %s" \
            % type(fileobj)
        io.BufferedReader.__init__(self, fileobj)
        # TODO: not sure if it is the best things to do...
        if sys.version_info < (2, 6, 5) and not hasattr(self, 'name'):
            self.name = getattr(fileobj, 'name', name)
        self.realname = name or ''
        self.source = source
        self.closefd = closefd
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
        assert hasattr(cls, '__mimes__'), \
            "this function is useless without __mimes__"
        realname = name
        match = re_extension.search(name)
        if hasattr(cls, '__extensions__') and \
           match.group(2) and \
           os.path.normcase(match.group(3)) in cls.__extensions__:
            realname = match.group(1)
        if mime not in cls.__mimes__:
            raise ValueError(
                (cls, mime, name, fileobj),
                "can not decompress fileobj using class %s" % cls.__name__)
        return realname

    def close(self):
        if self.closefd:
            super(Archive, self).close()
            self.source.close()

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
    def __init__(self, fileobj=None, name=None, closefd=True):
        if not fileobj:
            if not name:
                raise TypeError("Either name, fileobj must be specified")
            fileobj = io.FileIO(name)
        elif not name and hasattr(fileobj, 'name'):
            name = fileobj.name
        Archive.__init__(self, name, fileobj, source=fileobj, closefd=closefd)


class ArchiveTemp(Archive):
    """
    Write down a file-object to a temporary file and make an archive from it
    """
    def __init__(self, fileobj, name=None):
        if isinstance(fileobj, Archive):
            if name is None: name = fileobj.realname
        else:
            name = fileobj.name
        tempdir = \
            (os.path.dirname(name) if isinstance(name, basestring) else None)
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
        threading.Thread.__init__(self)
        self.p = Popen(self.__command__, stdout=PIPE, stdin=PIPE, stderr=PIPE)
        Archive.__init__(self, name, fileobj=self.p.stdout, source=stdin)
        self.start()

    @classmethod
    def __checkavailability__(cls):
        assert cls is not ExternalPipe, \
            "This class can not be used in standalone"
        assert hasattr(cls, '__command__'), \
            "__command__ attribute is missing in class %s" % cls
        commands = [cls.__command__[0]]
        if hasattr(cls, '__fallbackcommands__'):
            commands += cls.__fallbackcommands__
        existing_commands = filter(None, map(find_executable, commands))
        if not existing_commands:
            if len(commands) == 1:
                raise OSError(2, commands[0], "cannot find executable")
            else:
                raise OSError(2, commands[0],
                    "cannot find executable between: " + ", ".join(commands))
        cls.__command__[0] = existing_commands[0]

    def run(self):
        try:
            self.p.stdin.writelines(self.source)
        except IOError, exc:
            # NOTE: regular exception when we close the pipe, just hide it
            if not exc.errno == errno.EPIPE:
                raise
        else:
            self.p.stdin.close()

    @property
    def closed(self):
        return self.p.stdout.closed

    def close(self):
        if not self.closed:
            self.p.terminate()
            self.join()
            self.p.stdin.close()
            self.retcode = self.p.wait()
            self.errors = self.p.stderr.read()
            self.p.stderr.close()
            self.p.stdout.close()
