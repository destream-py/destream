from . import ExternalPipe

__all__ = ['Unxz']


class Unxz(ExternalPipe):
    __command__ = 'unxz -c'.split()
    __compressions__ = ['xz']
