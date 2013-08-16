gzip = __import__('gzip')

from . import Archive


class Gunzip(gzip.GzipFile, Archive):
    def __init__(self, archive, filename):
        Archive.__init__(self, filename, archive.compressions + ['gzip'])
        gzip.GzipFile.__init__(self, fileobj=archive)
