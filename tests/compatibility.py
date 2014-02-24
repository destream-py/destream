import sys

if sys.version_info < (2, 7):
    import tarfile

    # backported from Python-2.7
    def __enter__(self):
        self._check()
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.close()
        else:
            # An exception occurred. We must not call close() because
            # it would try to write end-of-archive blocks and padding.
            if not self._extfileobj:
                self.fileobj.close()
            self.closed = True

    tarfile.TarFile.__enter__ = __enter__
    tarfile.TarFile.__exit__ = __exit__

    # simplified __enter__
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.close()
        else:
            # An exception occurred. We must not call close() because
            # it would try to write end-of-archive blocks and padding.
            if not self.myfileobj:
                self.myfileobj.close()
            self.closed = True

    import gzip
    gzip.GzipFile.__enter__ = __enter__
    gzip.GzipFile.__exit__ = __exit__
