import os
import sys
from io import BytesIO
import gzip
import tarfile
import unittest2

import compatibility

import StreamDecompressor


class GuesserTest(unittest2.TestCase):
    def _check_decompressor(self,
            decompressor, compressed_fileobj, decompressed_fileobj):
        try:
            decompressor.__checkavailability__()
        except:
            self.skipTest("decompressor not available")
        with StreamDecompressor.open(fileobj=compressed_fileobj) as archive:
            self.assertEqual(
                archive.compressions,
                [decompressor.__compression__],
                "expected compressions does not match")
            if archive.seekable():
                self.assertEqual(archive.tell(), 0,
                    "the archive cursor should be on position 0")
            decompressed_fileobj.seek(0)
            if not isinstance(archive, StreamDecompressor.ArchivePack) \
               or archive.single():
                self.assertEqual(archive.read(), decompressed_fileobj.read(),
                    "content does not match")
            else:
                self.assertEqual(archive.read(), '',
                    "content should be empty for archive having multiple files")
                for fileobj in (archive.open(m) for m in archive.members()):
                    decompressed_fileobj.seek(0)
                    self.assertEqual(
                        fileobj.read(),
                        decompressed_fileobj.read(),
                        "content does not match")
            self.assertEqual(
                archive.realname + '.' + decompressor.__extensions__[0],
                compressed_fileobj.name,
                "expected archive name does not match")

    def test_10_plain_text(self):
        fileobj = BytesIO("Hello World\n")
        fileobj.name = "test_file.txt"
        guessed = StreamDecompressor.open(fileobj=fileobj)
        self.assertEqual(guessed.compressions, [],
            "should not have compressions")
        fileobj.seek(0)
        self.assertEqual(fileobj.read(), guessed.read(),
            "should have the same content")
        self.assertEqual(guessed.realname, fileobj.name)

    def test_20_external_pipe_lzma(self):
        uncompressed = BytesIO("Hello World\n")
        raw = BytesIO(
            ']\x00\x00\x80\x00\xff\xff\xff\xff\xff\xff\xff\xff\x00'
            '$\x19I\x98o\x10\x11\xc8_\xe6\xd5\x8a\x04\xda\x01\xc7'
            '\xff\xff\x0b8\x00\x00')
        raw.name = "test_file.lzma"
        self._check_decompressor(
            StreamDecompressor.decompressors.Unlzma,
            raw, uncompressed)

    def test_30_external_pipe_gzip(self):
        uncompressed = BytesIO("Hello World\n")
        raw = BytesIO()
        raw.name = "test_file.gz"
        with gzip.GzipFile(fileobj=raw, mode='wb') as compressed:
            compressed.writelines(uncompressed)
        self._check_decompressor(
            StreamDecompressor.decompressors.Gunzip,
            raw, uncompressed)

    def test_40_tar_single_file(self):
        uncompressed = BytesIO("Hello World\n")
        raw = BytesIO()
        raw.name = "test_file.tar"
        with tarfile.open(fileobj=raw, mode='w') as tar:
            tarinfo = tarfile.TarInfo('test_file')
            tarinfo.size = len(uncompressed.getvalue())
            tar.addfile(tarinfo, uncompressed)
        self._check_decompressor(
            StreamDecompressor.decompressors.Untar,
            raw, uncompressed)

    def test_50_tar_multiple_files(self):
        uncompressed = BytesIO("Hello World\n")
        raw = BytesIO()
        raw.name = "test_file.tar"
        with tarfile.open(fileobj=raw, mode='w') as tar:
            for filename in ('test_file1', 'test_file2'):
                tarinfo = tarfile.TarInfo(filename)
                tarinfo.size = len(uncompressed.getvalue())
                uncompressed.seek(0)
                tar.addfile(tarinfo, uncompressed)
        self._check_decompressor(
            StreamDecompressor.decompressors.Untar,
            raw, uncompressed)
