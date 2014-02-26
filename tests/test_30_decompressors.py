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

    def test_20_external_pipe_gzip(self):
        uncompressed = BytesIO("Hello World\n")
        raw = BytesIO()
        raw.name = "test_file.gz"
        with gzip.GzipFile(fileobj=raw, mode='wb') as compressed:
            compressed.writelines(uncompressed)
        self._check_decompressor(
            StreamDecompressor.decompressors.Gunzip,
            raw, uncompressed)

    def test_30_tar_single_file(self):
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

    def test_40_tar_multiple_files(self):
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

    def test_20_external_pipe_xz(self):
        uncompressed = BytesIO("Hello World\n")
        raw = BytesIO(
            '\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00'
            't/\xe5\xa3\x01\x00\x0bHello World\n\x00"\xe0u?\xd5\xed8>\x00\x01'
            '$\x0c\xa6\x18\xd8\xd8\x1f\xb6\xf3}\x01\x00\x00\x00\x00\x04YZ')
        raw.name = "test_file.xz"
        self._check_decompressor(
            StreamDecompressor.decompressors.Unxz,
            raw, uncompressed)

    def test_30_7z_single_file(self):
        uncompressed = BytesIO("Hello World\n")
        raws = [
            # no file, only the content is packed, use 7zr -si to make it
            BytesIO("7z\xbc\xaf'\x1c\x00\x03\\\x01\xca\xbe\x11\x00\x00\x00"
                "\x00\x00\x00\x00;\x00\x00\x00\x00\x00\x00\x00\xccl\x1bR\x00"
                "$\x19I\x98o\x10\x11\xc8_\xe6\xd5\x8a\x02\x8f\x14\x00\x01\x04"
                "\x06\x00\x01\t\x11\x00\x07\x0b\x01\x00\x01#\x03\x01\x01\x05]"
                "\x00\x00\x00\x01\x0c\x0c\x00\x08\n\x01\xe3\xe5\x95\xb0\x00"
                "\x00\x05\x01\x14\n\x01\x00\xc0\x8dZ!\xf62\xcf\x01\x15\x06"
                "\x01\x00\x00\x00\x00\x00\x00\x00"),
            # only one file, named, but same content
            BytesIO("7z\xbc\xaf'\x1c\x00\x03+v\xeet\x11\x00\x00\x00\x00\x00"
                "\x00\x00B\x00\x00\x00\x00\x00\x00\x00\x10\xb9\x06\x02\x00$"
                "\x19I\x98o\x10\x11\xc8_\xe6\xd5\x8a\x02\x8f\x14\x00\x01\x04"
                "\x06\x00\x01\t\x11\x00\x07\x0b\x01\x00\x01#\x03\x01\x01\x05"
                "]\x00\x00\x01\x00\x0c\x0c\x00\x08\n\x01\xe3\xe5\x95\xb0\x00"
                "\x00\x05\x01\x11\x05\x00a\x00\x00\x00\x14\n\x01\x00\x80]]\\"
                "\xf62\xcf\x01\x15\x06\x01\x00 \x80\xa4\x81\x00\x00"),
        ]
        for raw in raws:
            raw.name = "test_file.7z"
            self._check_decompressor(
                StreamDecompressor.decompressors.Un7z,
                raw, uncompressed)

    def test_40_7z_multiple_files(self):
        uncompressed = BytesIO("Hello World\n")
        raw = BytesIO(
            "7z\xbc\xaf'\x1c\x00\x035xN\x15`\x00\x00\x00\x00\x00\x00\x00 "
            "\x00\x00\x00\x00\x00\x00\x00`\x98\xfa\xcf\x00$\x19I\x98o\x10\x11"
            "\xc8_\xe6\xd5\x8a\x05U3\x9d`\x00\x00\x00\x813\x07\xae\x0f\xcf'"
            "\xf0\x8c\x07\xc8C\x80\x83\x81[\xff\xac\x80\x1dP\x19\xff\xf6\xf8"
            "\x17!l\xa9\xf9r\x19\x1b^y\xee#r\xd7\x12\xcdoh>\x03\xf3\xbf\xaf"
            "\xe47\x9b\x99\xd3\x9d\x0b\x17\xf0\xa1\xd0\x1d\ta\x91\xc8w\xd1"
            "\xee\x95\xa6\xe2\xbd\x8b\x81\x00\x00\x17\x06\x13\x01\tM\x00\x07"
            "\x0b\x01\x00\x01#\x03\x01\x01\x05]\x00\x10\x00\x00\x0cZ\n\x01"
            "\x15U\xfe\x8a\x00\x00")
        raw.name = "test_file.7z"
        self._check_decompressor(
            StreamDecompressor.decompressors.Un7z,
            raw, uncompressed)
