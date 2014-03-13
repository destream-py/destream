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
    __extensions__ = ['ext1', 'ext2']
    __mimes__ = ['mime1', 'mime2']


class Archive(unittest2.TestCase):
    def test_10_guess_basename(self):
        fileobj = BytesIO('')
        try:
            self.assertEqual(
                'xxx', BaseNameTest.__guess__('mime2', 'xxx', fileobj))
            self.assertEqual(
                'xxx', BaseNameTest.__guess__('mime1', 'xxx.ext2', fileobj))
            self.assertEqual(
                'xxx', BaseNameTest.__guess__('mime2', 'xxx.ext1', fileobj))
        except ValueError, e:
            self.fail(repr(e))
        try:
            self.assertEqual(
                'xxx', BaseNameTest.__guess__('xxx', 'xxx.ext1', fileobj))
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


class CatsEye(ExternalPipe):
    __command__ = ['cat']
    __priority__ = 10

    @classmethod
    def __guess__(cls, mime, name, archive):
        if cls in archive.__decompressors__:
            raise ValueError("oh no, not again!")
        print "don't skip"
        return name


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
        self.assertEqual(pipe.compressions, [])
        self.assertEqual(pipe.__decompressors__, [CatsEye])
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
