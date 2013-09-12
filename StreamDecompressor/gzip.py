from . import ExternalPipe

__all__ = ['Gunzip']


class Gunzip(ExternalPipe):
    __command__ = 'gunzip -c'.split()
    __compressions__ = ['gzip']
