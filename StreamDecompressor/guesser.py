import magic

from archive import ArchiveFile, ArchivePack, \
                    all_decompressors

__all__ = ['Guesser', 'open']


class Guesser(object):
    """
    Make a stream using the decompressors given in the constructor
    """
    def __init__(self, decompressors, limit=10):
        self.decompressors = list(decompressors)
        self.limit = limit

    def guess(self, archive):
        mime = magic.from_buffer(archive.peek(1024), mime=True)
        for decompressor in self.decompressors:
            try:
                realname = decompressor.__guess__(
                    mime, archive.realname, archive)
                decompressor.__checkavailability__()
                return decompressor(realname, archive)
            except AttributeError:
                pass
        return None

    def open(self, name=None, fileobj=None):
        archive = ArchiveFile(fileobj, name)
        archive.seek(0) # TODO should be useless

        for i in range(self.limit):
            guessed = self.guess(archive)
            if not guessed:
                return archive
            archive = guessed
            if isinstance(archive, ArchivePack) and not archive.single():
                return archive

        raise Exception("More than 10 pipes or infinite loop detected")


def open(name=None, fileobj=None):
    """
    Use all decompressor possible to make the stream
    """
    return Guesser(all_decompressors).open(name=name, fileobj=fileobj)
