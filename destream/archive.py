import re
import os
import io
import sys

__all__ = """
          Archive ArchivePack
          """.split()


RE_EXTENSION = re.compile(r"^(.*?)(\.([^.]+))?$")


class Archive(io.BufferedReader):
    """
    Base class to Archive file
    """

    def __init__(self, name, fileobj=None, source=None, closefd=True):
        assert (
            type(self) != Archive
        ), "This class can not be used in standalone"
        if not fileobj:
            fileobj = io.BytesIO()
        elif sys.version_info < (3, 0) and isinstance(fileobj, file):
            filename = fileobj.name
            fileobj = io.FileIO(fileobj.fileno(), closefd=False)
            fileobj.name = filename
        elif isinstance(fileobj, int):
            fileobj = io.FileIO(fileobj, closefd=False)
            fileobj.name = name
        assert isinstance(fileobj, io.IOBase), (
            f"fileobj must be an instance of io.IOBase or a file, "
            f"got {type(fileobj)}"
        )
        io.BufferedReader.__init__(self, fileobj)
        self.realname = name or ""
        self.source = source
        self.closefd = closefd
        if isinstance(source, Archive):
            self._decompressors = source._decompressors + [type(self)]
            self.compressions = list(source.compressions)
        else:
            self._decompressors = [type(self)]
            self.compressions = []
        if hasattr(self, "_compression"):
            self.compressions += [self._compression]

    @classmethod
    def _check_availability(self):
        pass

    @classmethod
    def _guess(cls, mime, name, fileobj):
        if getattr(cls, "_unique_instance", False):
            if cls in fileobj._decompressors:
                raise ValueError(
                    f"class {cls} already in the decompressor list"
                )
        realname = name
        if hasattr(cls, "_mimes"):
            match = RE_EXTENSION.search(name)
            if (
                hasattr(cls, "_extensions")
                and match.group(2)
                and os.path.normcase(match.group(3)) in cls._extensions
            ):
                realname = match.group(1)
            if mime not in cls._mimes:
                raise ValueError(
                    (cls, mime, name, fileobj),
                    f"can not decompress fileobj using class {cls.__name__}",
                )
        return realname

    def close(self):
        if getattr(self, "closefd", True):
            super().close()


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
            f"class {type(self)} does not implement this method"
        )

    def open(self, member):
        raise NotImplementedError(
            f"class {type(self)} does not implement this method"
        )

    def extract(self, member, path):
        raise NotImplementedError(
            f"class {type(self)} does not implement this method"
        )

    def extractall(self, path, members=None):
        raise NotImplementedError(
            f"class {type(self)} does not implement this method"
        )
