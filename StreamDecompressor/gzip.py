gzip = __import__('gzip')

from . import Archive


class Gunzip(gzip.GzipFile, Archive):
    def __init__(self, fileobj, filename):
        Archive.__init__(self, filename, fileobj.compressions + ['gzip'])
        gzip.GzipFile.__init__(self, fileobj=fileobj)
