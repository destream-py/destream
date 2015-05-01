from StreamDecompressor import ExternalPipe

__all__ = ['Unxz']


class Unxz(ExternalPipe):
    _mimes = ['application/x-xz']
    _extensions = ['xz']
    _command = 'unxz -c'.split()
    __compression = 'xz'
    _compression = 'xz'
