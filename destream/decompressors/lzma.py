from destream import ExternalPipe

__all__ = ['Unlzma']


class Unlzma(ExternalPipe):
    _mimes = ['application/x-lzma']
    _extensions = ['lzma']
    _command = 'unlzma -c'.split()
    _compression = 'lzma'
