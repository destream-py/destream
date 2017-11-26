from destream import ExternalPipe

__all__ = ['Unzstd']


class Unzstd(ExternalPipe):
    _mimes = ['application/x-zstd']
    _extensions = ['zst']
    _command = 'unzstd -c'.split()
    _compression = 'zstd'
