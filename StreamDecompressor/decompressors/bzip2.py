from StreamDecompressor import ExternalPipe

__all__ = ['Bunzip2']


class Bunzip2(ExternalPipe):
    __mimes__ = ['application/x-bzip2']
    _extensions = ['bz2', 'bz', 'tbz2', 'tbz']
    __command__ = ['bunzip2']
    _compression = 'bzip2'

    @classmethod
    def _guess(cls, mime, name, fileobj):
        is_tar = name.endswith('.tbz2') or name.endswith('.tbz')
        realname = super(Bunzip2, cls)._guess(mime, name, fileobj)
        return realname + '.tar' if is_tar else realname
