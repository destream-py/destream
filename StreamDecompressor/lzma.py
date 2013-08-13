from . import Archive, ExternalPipe


class Unlzma(ExternalPipe, Archive):
    def __init__(self, fileobj, filename):
        Archive.__init__(self, filename, fileobj.compressions + ['lzma'])
        ExternalPipe.__init__(self, ['unlzma','-c'], fileobj, filename)
