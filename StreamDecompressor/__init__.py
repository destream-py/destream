import os
import errno
from io import IOBase, BufferedReader, BytesIO, FileIO
from subprocess import Popen, PIPE


class Archive(BufferedReader):
    def __init__(self, name, compressions, fileobj=None,
            source=None, single=True):
        assert type(self) != Archive, \
            "This class can not be used in standalone"
        if not fileobj:
            fileobj = BytesIO()
        elif isinstance(fileobj, file):
            fileobj = FileIO(fileobj.fileno(), closefd=False)
        assert isinstance(fileobj, IOBase), \
            "fileobj must be an instance of io.IOBase or a file, got %s" \
            % type(fileobj)
        if not fileobj.seekable():
            fileobj, stream = BytesIO(), fileobj
            fileobj.writelines(stream)
            fileobj.seek(0)
        BufferedReader.__init__(self, fileobj)
        self.realname = name
        self.single = single
        self.source = source
        self.compressions = (source.compressions if isinstance(source, Archive)
            else []) + compressions


class ArchiveFile(Archive):
    def __init__(self, fileobj=None, name=None):
        if not fileobj:
            if not name:
                raise TypeError("Either name, fileobjmust be specified")
            fileobj = FileIO(name)
        elif not name:
                name = fileobj.name
        Archive.__init__(self, name, [], fileobj, single=True)


class ExternalPipe(Archive):
    def __init__(self, name, stdin):
        assert type(self) != ExternalPipe, \
            "This class can not be used in standalone"
        assert hasattr(self, '__command__'), \
            "__command__ attribute is missing in class %s" % type(self)
        assert hasattr(self, '__compressions__'), \
            "__compressions__ attribute is missing in class %s" % type(self)
        p = Popen(self.__command__, stdout=PIPE, stdin=PIPE)
        p.stdin.writelines(stdin)
        p.stdin.close()
        Archive.__init__(self, name, self.__compressions__, p.stdout,
            source=stdin, single=True)


from guesser import *
