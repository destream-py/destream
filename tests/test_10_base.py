import os
from io import BytesIO
import unittest2
import warnings

from StreamDecompressor import ArchiveFile, ExternalPipe

warnings.filterwarnings(
    'ignore',
    '^tmpnam is a potential security risk to your program$',
    RuntimeWarning,
    '^%s$' % __name__,
)


class ArchiveFileTest(unittest2.TestCase):
    def regular_tests(self, archive, fileobj, filename, text):
        self.assertEqual(archive.fileno(), fileobj.fileno(),
            "file no does not match!")
        self.assertEqual(archive.name, filename,
            "name attribute does not match!")
        archive.seek(0)
        self.assertEqual(archive.read(), text,
            "file content does not match!")

    def test_10_passing_file_object(self):
        text = "Hello World!\n"
        fileobj = os.tmpfile()
        fileobj.write(text)
        fileobj.flush()
        archive = ArchiveFile(fileobj=fileobj)
        self.regular_tests(archive, fileobj, fileobj.name, text)
        fileobj.close()

    def test_20_passing_filename(self):
        text = "Hello World!\n"
        filename = os.tmpnam()
        fileobj = open(filename, 'w+b')
        try:
            fileobj.write(text)
            fileobj.flush()
            archive = ArchiveFile(fileobj=fileobj)
            self.regular_tests(archive, fileobj, filename, text)
        finally:
            fileobj.close()
            os.unlink(filename)


class CatsEye(ExternalPipe):
    __command__ = ['cat']
    __compressions__ = ['cat']


class ExternalPipeTest(unittest2.TestCase):
    def regular_tests(self, pipe, filename, text):
        self.assertEqual(pipe.realname, filename,
            "name attribute does not match!")
        pipe.seek(0)
        self.assertEqual(pipe.read(), text,
            "file content does not match!")

    def test_10_check_output(self):
        text = "Hello World\n"
        filename = '<pipe_test>'
        fileobj = BytesIO(text)
        pipe = CatsEye(filename, fileobj)
        pipe.read()
        self.assertEqual(pipe.read(), '',
            "should be the end of file")
        self.assertEqual(CatsEye.__compressions__, pipe.compressions)
        self.regular_tests(pipe, filename, text)
