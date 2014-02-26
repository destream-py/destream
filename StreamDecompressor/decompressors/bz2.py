from StreamDecompressor import ExternalPipe

__all__ = ['Bunzip2']


class Bunzip2(ExternalPipe):
    __mimes__ = ['application/x-bzip2']
    __extensions__ = ['bz2']
    __command__ = ['bunzip2']
    __compression__ = 'bz2'
