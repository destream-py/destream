import re
import os
import sys
import errno
import io
import tempfile
from shutil import copyfileobj
from subprocess import Popen, PIPE
import threading
from distutils.spawn import find_executable

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
            fileobj.name = filename
        elif isinstance(fileobj, int):
            fileobj = io.FileIO(fileobj, closefd=False)
            fileobj.name = name
        assert isinstance(fileobj, io.IOBase), \
            "fileobj must be an instance of io.IOBase or a file, got %s" \
            % type(fileobj)
        io.BufferedReader.__init__(self, fileobj)
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
        if getattr(cls, '__uniqueinstance__', False):
            if cls in fileobj.__decompressors__:
                raise ValueError("class %s already in the decompressor list")
        realname = name
        if hasattr(cls, '__mimes__'):
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
        if getattr(self, 'closefd', True):
            super(Archive, self).close()

    def __del__(self):
        self.close()
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
        raise NotImplementedError(
            "class %s does not implement this method" % type(self))

    def open(self, member):
        raise NotImplementedError(
            "class %s does not implement this method" % type(self))

    def extract(self, member, path):
        raise NotImplementedError(
            "class %s does not implement this method" % type(self))

    def extractall(self, path, members=None):
        raise NotImplementedError(
            "class %s does not implement this method" % type(self))


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
        # NOTE: no need (and you shouldn't need) to close the temporary file,
        #       it will be automatically closed on __del__()
        fileio = io.FileIO(self.tempfile.fileno(), closefd=False)
        fileio.name = self.tempfile.name
        Archive.__init__(self, name, fileio, source=fileobj)


def make_seekable(fileobj):
    """
    If the file-object is not seekable, return  ArchiveTemp of the fileobject,
    otherwise return the file-object itself
    """
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
            copyfileobj(self.source, self.p.stdin)
        except IOError, exc:
            # NOTE: regular exception when we close the pipe, just hide it
            if not exc.errno == errno.EPIPE:
                raise
        self.p.stdin.close()
        self.p.wait()

    @property
    def closed(self):
        return self.p.stdout.closed

    def close(self):
        super(ExternalPipe, self).close()
        if self.p.poll() is None:
            self.p.terminate()
            self.join()
