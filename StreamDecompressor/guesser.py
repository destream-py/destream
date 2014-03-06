import magic

from archive import ArchiveFile, ArchivePack
from decompressors import builtin_decompressors

__all__ = ['Guesser', 'open']


class Guesser(object):
    """
    Make a stream using the decompressors given in the constructor
    """
    def __init__(self, decompressors=builtin_decompressors,
                 extra_decompressors=[], limit=10):
        self.decompressors = sorted(decompressors + extra_decompressors)
        self.limit = limit

    def guess(self, archive):
        mime = magic.from_buffer(archive.peek(1024), mime=True)
        for _, decompressor in self.decompressors:
            if isinstance(archive, ArchivePack) and \
               type(archive) is decompressor:
                continue
            try:
                realname = decompressor.__guess__(
                    mime, archive.realname, archive)
                decompressor.__checkavailability__()
                return decompressor(realname, archive)
            except ValueError:
                pass
        return None

    def open(self, name=None, fileobj=None):
        archive = ArchiveFile(fileobj, name)

        for i in range(self.limit):
            guessed = self.guess(archive)
            if not guessed:
                return archive
            archive = guessed

        raise Exception("More than 10 pipes or infinite loop detected")


def open(name=None, fileobj=None):
    """
    Use all decompressor possible to make the stream
    """
    return Guesser().open(name=name, fileobj=fileobj)
