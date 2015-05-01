import os
from io import BytesIO
import unittest2
import warnings

from StreamDecompressor import Archive, ArchiveFile, ArchiveTemp, ExternalPipe

warnings.filterwarnings(
    'ignore',
    '^tmpnam is a potential security risk to your program$',
    RuntimeWarning,
    '^%s$' % __name__,
)


class BaseNameTest(Archive):
    _extensions = ['ext1', 'ext2']
    _mimes = ['mime1', 'mime2']


class Archive(unittest2.TestCase):
    def test_10_guess_basename(self):
        fileobj = BytesIO('')
        try:
            self.assertEqual(
                'xxx', BaseNameTest._guess('mime2', 'xxx', fileobj))
            self.assertEqual(
                'xxx', BaseNameTest._guess('mime1', 'xxx.ext2', fileobj))
            self.assertEqual(
                'xxx', BaseNameTest._guess('mime2', 'xxx.ext1', fileobj))
        except ValueError, e:
            self.fail(repr(e))
        try:
            self.assertEqual(
                'xxx', BaseNameTest._guess('xxx', 'xxx.ext1', fileobj))
        except ValueError, e:
            pass
        else:
            self.fail("guessing should has failed")


class ArchiveFileTest(unittest2.TestCase):
    def _regular_tests(self, archive, fileobj, filename, text):
        self.assertEqual(
            archive.fileno(),
            fileobj.fileno(),
            "file no does not match!")
        self.assertEqual(archive.name, filename,
            "name attribute does not match!")
        archive.seek(0)
        self.assertEqual(archive.read(), text,
            "file content does not match!")

    def test_10_passing_file_object(self):
        text = "Hello World!\n"
        with os.tmpfile() as fileobj:
            fileobj.write(text)
            fileobj.flush()
            archive = ArchiveFile(fileobj=fileobj)
            self._regular_tests(archive, fileobj, fileobj.name, text)

    def test_20_passing_filename(self):
        text = "Hello World!\n"
        filename = os.tmpnam()
        fileobj = open(filename, 'w+b')
        try:
            fileobj.write(text)
            fileobj.flush()
            archive = ArchiveFile(fileobj=fileobj)
            self._regular_tests(archive, fileobj, filename, text)
        finally:
            fileobj.close()
            os.unlink(filename)

    def test_30_closefd(self):
        fileobj = BytesIO()
        archive = ArchiveFile(fileobj=fileobj, closefd=False)
        archive.close()
        self.assertFalse(fileobj.closed)
        archive = ArchiveFile(fileobj=fileobj, closefd=True)
        archive.close()
        self.assertTrue(fileobj.closed)


class CatsEye(ExternalPipe):
    _command = ['cat']
    _compression = 'cat'
    _unique_instance = True
    __priority__ = 10


class ExternalPipeTest(unittest2.TestCase):
    def _regular_tests(self, pipe, filename, text):
        self.assertEqual(pipe.realname, filename,
            "name attribute does not match!")
        self.assertEqual(pipe.read(), text, "file content does not match!")
        self.assertEqual(pipe.read(), '', "should be the end of file")

    def test_10_check_output(self):
        text = "Hello World\n"
        filename = '<pipe_test>'
        fileobj = BytesIO(text)
        pipe = CatsEye(filename, fileobj)
        try:
            CatsEye._guess('', filename, pipe)
        except ValueError:
            pass
        else:
            self.fail("CatsEye is _unique_instance = True")
        self.assertEqual(pipe.compressions, ['cat'])
        self.assertEqual(pipe._decompressors, [CatsEye])
        self._regular_tests(pipe, filename, text)


class ArchiveTempTest(unittest2.TestCase):
    def test_10_create_temp_archive_from_externalpipe(self):
        text = "Hello World\n"
        filename = os.tmpnam()
        fileobj = BytesIO(text)
        pipe = CatsEye(filename, fileobj)
        temp = ArchiveTemp(pipe)
        self.assertEqual(pipe.read(), '', "should be the end of file")
        self.assertEqual(
            os.path.dirname(filename),
            os.path.dirname(temp.name),
            "Temp file and temp archive should be in the same directory")
        self.assertEqual(temp.read(), text)
