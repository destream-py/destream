gzip = __import__('gzip')

from . import Archive


class Gunzip(Archive):
    def __init__(self, name, fileobj):
        Archive.__init__(self, name, ['gzip'], gzip.GzipFile(fileobj=fileobj),
            source=fileobj, single=True)
