from StreamDecompressor import ExternalPipe

__all__ = ['Bunzip2']


class Bunzip2(ExternalPipe):
    __mimes__ = ['application/x-bzip2']
    __extensions__ = ['bz2', 'bz', 'tbz2', 'tbz']
    __command__ = ['bunzip2']
    __compression__ = 'bzip2'

    @classmethod
    def __guess__(cls, mime, name, fileobj):
        is_tar = name.endswith('.tbz2') or name.endswith('.tbz')
        realname = super(Bunzip2, cls).__guess__(mime, name, fileobj)
        return realname + '.tar' if is_tar else realname
