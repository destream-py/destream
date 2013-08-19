from . import ExternalPipe

__all__ = ['Unlzma']


class Unlzma(ExternalPipe):
    __command__ = 'unlzma -c'.split()
    __compressions__ = ['lzma']
