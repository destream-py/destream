import re
import os
import sys
import errno
import io
import tempfile
from subprocess import Popen, PIPE
import threading

if sys.version_info < (2, 7):
    io_name_attr = '_name'
else:
    io_name_attr = 'name'

__all__ = """\
        Archive ArchivePack ArchiveFile ArchiveTemp ExternalPipe
        make_seekable all_decompressors
    """.split()


all_decompressors = []

class MetaArchive(type):
    """
    Register all possible decompressor automatically
    """
    def __init__(cls, name, bases, dict):
        if dict['__module__'] != __name__:
            all_decompressors.append(cls)

# resolve conflict meta class when using io from Python-2.6
if sys.version_info < (2, 7):
    class MetaArchive(MetaArchive, io.BufferedReader.__metaclass__):
        pass

re_extension = re.compile('^(.*?)(\.([^.]+))?$')

class Archive(io.BufferedReader):
    """
    Base class to Archive file
    """
    __metaclass__ = MetaArchive

    def __init__(self, name, compressions, fileobj=None, source=None):
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
        if sys.version_info < (2, 6, 5):
            self.name = name
        self.realname = name or ''
        self.source = source
        self.compressions = (source.compressions if isinstance(source, Archive)
            else []) + compressions

    @classmethod
    def __checkavailability__(self):
        return True

    @classmethod
    def __guess__(cls, mime, name, fileobj):
        match = re_extension.search(name)
        if mime in cls.__mimes__:
            return match.group(1)
        if match.group(2) and match.group(3) in cls.__extensions__:
            return match.group(1)
        return None


class ArchivePack(Archive):
    """
    Base class for an archive that is also a pack of file (tar, zip, ...)
    """
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
        Archive.__init__(self, name, [], fileobj, source=fileobj)


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
        Archive.__init__(self, name, [], fileio, source=fileobj)


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

    # TODO
    #@classmethod
    #def __guess__(self, mime, name, fileobj):

    def run(self):
        self.p.stdin.writelines(self.stdin)
        self.p.stdin.close()
