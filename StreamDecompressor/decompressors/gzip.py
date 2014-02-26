from StreamDecompressor import ExternalPipe

__all__ = ['Gunzip']


class Gunzip(ExternalPipe):
    __mimes__ = ['application/x-gzip']
    __extensions__ = ['gz']
    __command__ = ['gunzip']
    __compression__ = 'gzip'
