import os
import sys
from io import BytesIO
import gzip
import tarfile
import unittest2

import compatibility

import StreamDecompressor
from StreamDecompressor import determine_mime


class GuesserTest(unittest2.TestCase):
    def test_10_plain_text(self):
        text = "Hello World\n"
        fileobj = BytesIO(text)
        fileobj.name = "test_file.txt"
        guessed = StreamDecompressor.open(fileobj=fileobj)
        self.assertEqual(guessed.compressions, [],
            "should not have compressions")
        fileobj.seek(0)
        a = fileobj.read()
        if sys.version_info < (2, 7):
            # guessed and fileobj have the same cursor
            guessed.seek(0)
            b = fileobj.read()
        else:
            # guessed and fileobj does not manage the same cursor
            guessed.seek(0)
            b = guessed.read()
        self.assertEqual(a, b,
            "should have the same content")
        self.assertEqual(guessed.realname, fileobj.name)

    def test_20_external_pipe_lzma(self):
        text = "Hello World\n"
        raw = BytesIO(']\x00\x00\x80\x00\xff\xff\xff\xff\xff\xff\xff\xff\x00'
                      '$\x19I\x98o\x10\x11\xc8_\xe6\xd5\x8a\x04\xda\x01\xc7'
                      '\xff\xff\x0b8\x00\x00')
        raw.name = "test_file.lzma"
        guessed = StreamDecompressor.open(fileobj=raw)
        self.assertEqual(guessed.compressions, ['lzma'])
        self.assertEqual(guessed.read(), text,
            "content does not match")
        self.assertEqual(guessed.realname + '.lzma', raw.name)

    def test_30_gzip(self):
        text = "Hello World\n"
        raw = BytesIO()
        raw.name = "test_file.gz"
        with gzip.GzipFile(fileobj=raw, mode='wb') as compressed:
            compressed.write(text)
        guessed = StreamDecompressor.open(fileobj=raw)
        self.assertEqual(guessed.compressions, ['gzip'])
        self.assertEqual(guessed.read(), text,
            "content does not match")
        self.assertEqual(guessed.realname + '.gz', raw.name)

    def test_40_tar_single_file(self):
        text = "Hello World\n"
        raw = BytesIO()
        raw.name = "test_file.tar"
        with tarfile.open(fileobj=raw, mode='w') as tar:
            tarinfo = tarfile.TarInfo('test_file')
            tarinfo.size = len(text)
            tar.addfile(tarinfo, BytesIO(text))
        with StreamDecompressor.open(fileobj=raw) as guessed:
            self.assertEqual(guessed.compressions, ['tar'])
            self.assertEqual(guessed.read(), text,
                "content does not match")
            self.assertEqual(guessed.realname + '.tar', raw.name)

    def test_50_tar_multiple_files(self):
        text = "Hello World\n"
        raw = BytesIO()
        raw.name = "test_file.tar"
        with tarfile.open(fileobj=raw, mode='w') as tar:
            for filename in ('test_file1', 'test_file2'):
                tarinfo = tarfile.TarInfo(filename)
                tarinfo.size = len(text)
                tar.addfile(tarinfo, BytesIO(text))
        with StreamDecompressor.open(fileobj=raw) as guessed:
            self.assertEqual(guessed.compressions, ['tar'])
            self.assertEqual(guessed.read(), '',
                "content should be empty for tarfiles with multiple files")
            self.assertEqual(guessed.realname + '.tar', raw.name)
            for member in guessed.tarfile.getmembers():
                fileobj = guessed.tarfile.extractfile(member)
                self.assertEqual(fileobj.read(), text,
                    "content does not match")
