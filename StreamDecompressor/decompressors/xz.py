from StreamDecompressor import ExternalPipe

__all__ = ['Unxz']


class Unxz(ExternalPipe):
    __mimes__ = ['application/x-xz']
    __extensions__ = ['xz']
    __command__ = 'unxz -c'.split()
    __compression__ = 'xz'
