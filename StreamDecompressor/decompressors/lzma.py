from StreamDecompressor import ExternalPipe

__all__ = ['Unlzma']


class Unlzma(ExternalPipe):
    _mimes = ['application/x-lzma']
    _extensions = ['lzma']
    __command__ = 'unlzma -c'.split()
    __compression = 'lzma'
    _compression = 'lzma'
