from . import Archive, ExternalPipe

__all__ = ['Unlzma']

path = 'unlzma'


class Unlzma(ExternalPipe, Archive):
    def __init__(self, archive, filename):
        Archive.__init__(self, filename, archive.compressions + ['lzma'])
        ExternalPipe.__init__(self, [path,'-c'], archive, filename)
