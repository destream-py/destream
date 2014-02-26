from StreamDecompressor import ExternalPipe

__all__ = ['Unlzma']


class Unlzma(ExternalPipe):
    __mimes__ = ['application/x-lzma']
    __extensions__ = ['lzma']
    __command__ = 'unlzma -c'.split()
    __compression__ = 'lzma'
