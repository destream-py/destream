import magic

from destream import ArchiveFile, ArchivePack, builtin_decompressors

__all__ = """
          Guesser open
          """.split()


class Guesser(object):
    """
    Make a stream using the decompressors given in the constructor
    """
    def __init__(self, decompressors=builtin_decompressors,
                 extra_decompressors=[], limit=10):
        self.decompressors = decompressors + extra_decompressors
        self.limit = limit

    def guess(self, archive):
        mime = magic.from_buffer(archive.peek(1024), mime=True)
        for _, decompressor in sorted(self.decompressors, key=lambda x: x[0]):
            if isinstance(archive, ArchivePack) and \
               type(archive) is decompressor:
                continue
            try:
                realname = decompressor._guess(
                    mime, str(archive.realname), archive)
                decompressor._check_availability()
                return decompressor(realname, archive)
            except ValueError:
                pass
        return None

    def open(self, name=None, fileobj=None, closefd=True):
        archive = ArchiveFile(fileobj, name, closefd=closefd)

        for i in range(self.limit):
            guessed = self.guess(archive)
            if not guessed:
                return archive
            archive = guessed

        raise Exception("More than 10 pipes or infinite loop detected")


def open(name=None, fileobj=None, closefd=True):
    """
    Use all decompressor possible to make the stream
    """
    return Guesser().open(name=name, fileobj=fileobj, closefd=closefd)
