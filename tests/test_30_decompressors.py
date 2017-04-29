import gzip
import os
import tempfile
import shutil
import sys
from io import BytesIO
import tarfile
import zipfile
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import destream


class GuesserTest(unittest.TestCase):
    def _check_decompressor(self, decompressor, compressed_fileobj,
            decompressed_fileobj, expected_name=None):
        try:
            decompressor._check_availability()
        except AttributeError:
            raise
        except Exception:
            self.skipTest("decompressor not available")
        if expected_name is None:
            expected_name = decompressed_fileobj.name
        with destream.open(
                fileobj=compressed_fileobj, closefd=False) as archive:
            # check that the decompressor has been used
            self.assertIn(
                decompressor,
                archive._decompressors, "the decompressor didn't apply")
            self.assertIn(
                decompressor._compression,
                (x.split(':')[0] for x in archive.compressions),
                "archive's compressions is bad")
            # check that the cursor is at the beginning of the file
            # (not available for streams)
            if archive.seekable():
                self.assertEqual(archive.tell(), 0,
                    "the archive cursor should be on position 0")
            # check that the realname with extension match the source realname
            if not isinstance(archive, destream.ArchivePack) \
               or archive.single():
                self.assertEqual(archive.read(), decompressed_fileobj.read(),
                    "content does not match")
                # check that the realname of archive is the same than the
                # single file member
                if isinstance(archive, destream.ArchivePack):
                    filename = getattr(archive.members()[0], 'filename',
                        getattr(archive.members()[0], 'name', None))
                    self.assertEqual(
                        archive.realname, os.path.basename(filename),
                        "the archive should have a realname set on the "
                        "single member's filename")
                if expected_name is not None:
                    self.assertEqual(
                        archive.realname, expected_name,
                        "the file inside the archive does not have "
                        "the right name")
            else:
                # check that archive realname with extension match its source
                # realname
                self.assertEqual(
                    archive.realname + '.'
                        + decompressor._extensions[0],
                    archive.source.realname,
                    "expected archive name does not match")

                # test source archive
                archive.seek(0)
                archive_content = archive.read()
                archive.source.seek(0)
                source_content = archive.source.read()
                self.assertEqual(archive.read(), archive.source.read(),
                    "content should have the same content than source archive "
                    "for archives having multiple files")
                # test open()
                # TODO: depending on the decompressor, open() should be tested
                # with different arguments (like stream=False)
                for fileobj in (archive.open(m) for m in archive.members()):
                    decompressed_fileobj.seek(0)
                    self.assertEqual(
                        fileobj.read(),
                        decompressed_fileobj.read(),
                        "content does not match")
                # test extract()
                tempdir = tempfile.mkdtemp()
                try:
                    for member in archive.members():
                        if hasattr(member, 'isfile') and not member.isfile():
                            continue
                        archive.extract(member, tempdir)
                        filename = getattr(member, 'filename',
                            getattr(member, 'name', None))
                        if filename is None:
                            raise AttributeError(
                                "%s instance has no attribute 'filename' nor "
                                "'name'" % (type(member).__name__))
                        filepath = os.path.join(tempdir, filename)
                        self.assertTrue(os.path.isfile(filepath),
                            "can not extract using extract() method: "
                            + filepath)
                finally:
                    shutil.rmtree(tempdir)
                # test extractall()
                tempdir = tempfile.mkdtemp()
                try:
                    archive.extractall(tempdir)
                    for member in archive.members():
                        filename = getattr(member, 'filename',
                            getattr(member, 'name', None))
                        if filename is None:
                            raise AttributeError(
                                "%s instance has no attribute 'filename' nor "
                                "'name'" % (type(member).__name__))
                        filepath = os.path.join(tempdir, filename)
                        self.assertTrue(os.path.exists(filepath),
                            "can not extract using extract() method: "
                            + filepath)
                finally:
                    shutil.rmtree(tempdir)
        # force closing archive by deleting the instance
        archive = None
        self.assertFalse(compressed_fileobj.closed)
        self.assertFalse(decompressed_fileobj.closed)

    def test_10_plain_text(self):
        fileobj = BytesIO(b"Hello World\n")
        fileobj.name = "test_file.txt"
        guessed = destream.open(fileobj=fileobj)
        self.assertEqual(guessed.compressions, [],
            "should not have compressions")
        fileobj.seek(0)
        self.assertEqual(fileobj.read(), guessed.read(),
            "should have the same content")
        self.assertEqual(guessed.realname, fileobj.name)

    def test_20_external_pipe_lzma(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = 'test_file'
        raw = BytesIO(
            b']\x00\x00\x80\x00\xff\xff\xff\xff\xff\xff\xff\xff\x00'
            b'$\x19I\x98o\x10\x11\xc8_\xe6\xd5\x8a\x04\xda\x01\xc7'
            b'\xff\xff\x0b8\x00\x00')
        raw.name = "test_file.lzma"
        self._check_decompressor(
            destream.decompressors.Unlzma,
            raw, uncompressed)

    def test_20_external_pipe_gzip(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = 'test_file'
        raw = BytesIO(
            b'\x1f\x8b\x08\x00\x96\xfa\rS\x00\x03\xf3H\xcd\xc9\xc9W\x08\xcf'
            b'/\xcaI\xe1\x02\x00\xe3\xe5\x95\xb0\x0c\x00\x00\x00')
        for ext, expected_name in [
                    ('.gz', uncompressed.name),
                    ('.GZ', uncompressed.name),
                    ('-gz', uncompressed.name),
                    ('.z', uncompressed.name),
                    ('-z', uncompressed.name),
                    ('_z', uncompressed.name),
                    ('.tgz', uncompressed.name + '.tar'),
                    ('.taz', uncompressed.name + '.tar'),
                    ('.TAZ', uncompressed.name + '.tar'),
                ]:
            uncompressed.seek(0)
            raw.seek(0)
            raw.name = "test_file" + ext
            self._check_decompressor(
                destream.decompressors.Gunzip,
                raw, uncompressed, expected_name)

    def test_30_tar_single_file(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = 'test_file'
        raw = BytesIO()
        raw.name = "test_file.tar"
        tar = tarfile.open(fileobj=raw, mode='w')
        try:
            tarinfo = tarfile.TarInfo(uncompressed.name)
            tarinfo.size = len(uncompressed.getvalue())
            tar.addfile(tarinfo, uncompressed)
            uncompressed.seek(0)
        finally:
            tar.close()
        raw.seek(0)
        self._check_decompressor(
            destream.decompressors.Untar,
            raw, uncompressed)

    def test_40_tar_multiple_files(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = None
        raw = BytesIO()
        raw.name = "test_file.tar"
        tar = tarfile.open(fileobj=raw, mode='w')
        try:
            for filename in ('a/test_file1', 'b/test_file2'):
                tarinfo = tarfile.TarInfo(filename)
                tarinfo.size = len(uncompressed.getvalue())
                uncompressed.seek(0)
                tar.addfile(tarinfo, uncompressed)
        finally:
            tar.close()
        raw.seek(0)
        self._check_decompressor(
            destream.decompressors.Untar,
            raw, uncompressed)

    def test_20_external_pipe_xz(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = 'test_file'
        raw = BytesIO(
            b'\xfd7zXZ\x00\x00\x04\xe6\xd6\xb4F\x02\x00!\x01\x16\x00\x00\x00'
            b't/\xe5\xa3\x01\x00\x0bHello World\n\x00"\xe0u?\xd5\xed8>\x00\x01'
            b'$\x0c\xa6\x18\xd8\xd8\x1f\xb6\xf3}\x01\x00\x00\x00\x00\x04YZ')
        raw.name = "test_file.xz"
        self._check_decompressor(
            destream.decompressors.Unxz,
            raw, uncompressed)

    def test_30_7z_single_file(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = None
        # no file, only the content is packed, use 7zr -si to make it
        raw = BytesIO(b"7z\xbc\xaf'\x1c\x00\x03\\\x01\xca\xbe\x11\x00\x00\x00"
            b"\x00\x00\x00\x00;\x00\x00\x00\x00\x00\x00\x00\xccl\x1bR\x00"
            b"$\x19I\x98o\x10\x11\xc8_\xe6\xd5\x8a\x02\x8f\x14\x00\x01\x04"
            b"\x06\x00\x01\t\x11\x00\x07\x0b\x01\x00\x01#\x03\x01\x01\x05]"
            b"\x00\x00\x00\x01\x0c\x0c\x00\x08\n\x01\xe3\xe5\x95\xb0\x00"
            b"\x00\x05\x01\x14\n\x01\x00\xc0\x8dZ!\xf62\xcf\x01\x15\x06"
            b"\x01\x00\x00\x00\x00\x00\x00\x00")
        self._check_decompressor(
            destream.decompressors.Un7z,
            raw, uncompressed)
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = 'a'
        # only one file, named, but same content
        raw = BytesIO(b"7z\xbc\xaf'\x1c\x00\x03+v\xeet\x11\x00\x00\x00\x00\x00"
            b"\x00\x00B\x00\x00\x00\x00\x00\x00\x00\x10\xb9\x06\x02\x00$"
            b"\x19I\x98o\x10\x11\xc8_\xe6\xd5\x8a\x02\x8f\x14\x00\x01\x04"
            b"\x06\x00\x01\t\x11\x00\x07\x0b\x01\x00\x01#\x03\x01\x01\x05"
            b"]\x00\x00\x01\x00\x0c\x0c\x00\x08\n\x01\xe3\xe5\x95\xb0\x00"
            b"\x00\x05\x01\x11\x05\x00a\x00\x00\x00\x14\n\x01\x00\x80]]\\"
            b"\xf62\xcf\x01\x15\x06\x01\x00 \x80\xa4\x81\x00\x00")
        raw.name = "test_file.7z"
        self._check_decompressor(
            destream.decompressors.Un7z,
            raw, uncompressed)

    def test_40_7z_multiple_files(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = None
        raw = BytesIO(
            b'7z\xbc\xaf\'\x1c\x00\x03\x10\xads\x82x\x00\x00\x00\x00\x00\x00'
            b'\x00!\x00\x00\x00\x00\x00\x00\x00\x7f$\xaa\x86\x00$\x19I\x98o'
            b'\x10\x11\xc8_\xe6\xd5\x8a\x05U3\x9d`\x00\x00\x00\x813\x07\xae'
            b'\x0f\xcf\'\xf0\x8c\x07\xc8C\x80\x83\x81[\xff\xac\x80\x1dP\x19'
            b'\xff\xf6\xf8\x17!l\xa9\xf9r\x19\x1b^y\xee#r\xd7\x15\xd2\xfc\xe1'
            b'\x17\xfa\xaa"\xafV\x05\xd7>\x1c\xf5\x93\xb5!R\x11\xdcMP\xf6\xab'
            b'\xc7\xd5\xc9\xbdj*{\xffp\x81\xbd\xf9\xbd\xf3\x87W\xfe\xa3F\xa3~&'
            b'(\xdc{\xd4\xb6Z\x9d\x98Dj \x00\x00\x17\x06\x13\x01\te\x00\x07'
            b'\x0b\x01\x00\x01#\x03\x01\x01\x05]\x00\x10\x00\x00\x0c\x80\x85'
            b'\n\x01pF\xbb5\x00\x00')
        raw.name = "test_file.7z"
        self._check_decompressor(
            destream.decompressors.Un7z,
            raw, uncompressed)

    def test_30_zip_single_file(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = 'test_file'
        raw = BytesIO()
        raw.name = "test_file.zip"
        zip = zipfile.ZipFile(raw, 'w')
        try:
            zip.writestr("test_file", uncompressed.getvalue())
        finally:
            zip.close()
        raw.seek(0)
        self._check_decompressor(
            destream.decompressors.Unzip,
            raw, uncompressed)

    def test_40_zip_multiple_files(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = None
        raw = BytesIO()
        raw.name = "test_file.zip"
        zip = zipfile.ZipFile(raw, 'w')
        try:
            for filename in ('a/test_file1', 'b/test_file2'):
                zip.writestr(filename, uncompressed.getvalue())
        finally:
            zip.close()
        raw.seek(0)
        self._check_decompressor(
            destream.decompressors.Unzip,
            raw, uncompressed)

    def test_20_external_pipe_bzip2(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = "test_file"
        raw = BytesIO(
            b'BZh91AY&SY\xd8r\x01/\x00\x00\x01W\x80\x00\x10@\x00\x00@\x00'
            b'\x80\x06\x04\x90\x00 \x00"\x06\x86\xd4 \xc9\x88\xc7i\xe8(\x1f'
            b'\x8b\xb9"\x9c(Hl9\x00\x97\x80')
        for ext, expected_name in [
                    ('.bz2', uncompressed.name),
                    ('.bz', uncompressed.name),
                    ('.tbz', uncompressed.name + '.tar'),
                    ('.tbz2', uncompressed.name + '.tar'),
                ]:
            uncompressed.seek(0)
            raw.seek(0)
            raw.name = "test_file" + ext
            self._check_decompressor(
                destream.decompressors.Bunzip2,
                raw, uncompressed, expected_name)

    def test_30_rar_single_file(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = 'a'
        raw = BytesIO(
            b"Rar!\x1a\x07\x00\xcf\x90s\x00\x00\r\x00\x00\x00\x00\x00\x00\x00"
            b"\x98\xdct \x90#\x00\x19\x00\x00\x00\x0c\x00\x00\x00\x03\xe3\xe5"
            b"\x95\xb0\x05|[D\x1d3\x01\x00\xa4\x81\x00\x00a\x00\xc0\x0c\x0c"
            b"\xcb\xec\xcb\xf1\x14'\x04\x18\x81\x0e\xec\x9aL\xff\xe3?\xfe\xcf"
            b"\x05z\x99\xd5\x10\xc4={\x00@\x07\x00")
        raw.name = "test_file.rar"
        self._check_decompressor(
            destream.decompressors.Unrar,
            raw, uncompressed)

    def test_40_rar_multiple_files(self):
        uncompressed = BytesIO(b"Hello World\n")
        uncompressed.name = None
        raw = BytesIO(
            b"Rar!\x1a\x07\x00\xcf\x90s\x00\x00\r\x00\x00\x00\x00\x00\x00\x00"
            b"d\xd9t \x80#\x00\x19\x00\x00\x00\x0c\x00\x00\x00\x03\xe3\xe5\x95"
            b"\xb07T\\D\x1d3\x03\x00\xa4\x81\x00\x00a\\b\x0c\x0c\xcb\xec\xcb"
            b"\xf1\x14'\x04\x18\x81\x0e\xec\x9aL\xff\xe3?\xfe\xcf\x05z\x99\xd5"
            b"\x10\x054t \x90%\x00\x19\x00\x00\x00\x0c\x00\x00\x00\x03\xe3\xe5"
            b"\x95\xb0=T\\D\x1d3\x03\x00\xa4\x81\x00\x00c\\d\x00\xc0\x0c\x0c"
            b"\xcb\xec\xcb\xf1\x14'\x04\x18\x81\x0e\xec\x9aL\xff\xe3?\xfe\xcf"
            b"\x05z\x99\xd5\x10\x98~t\xe0\x80!\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x03\x00\x00\x00\x007T\\D\x140\x01\x00\xedA\x00\x00a[\x99t"
            b"\xe0\x90#\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00"
            b"\x00=T\\D\x140\x01\x00\xedA\x00\x00c\x00\xc0\xc4={\x00@\x07\x00")
        raw.name = "test_file.rar"
        self._check_decompressor(
            destream.decompressors.Unrar,
            raw, uncompressed)

    def test_50_object_closed_on_delete(self):
        with tempfile.NamedTemporaryFile('w+b') as fh:
            # NOTE: the file must be big enough
            with gzip.open(fh.name, 'w+b') as gzipped:
                for i in range(3000):
                    gzipped.write(os.urandom(1024))
            archive = destream.open(fh.name)
            self.assertIn(
                destream.decompressors.Gunzip,
                archive._decompressors)
            proc = archive.p
            thread = archive.t
            del archive
            self.assertIsNotNone(proc.poll())
            self.assertFalse(thread.is_alive())
            archive2 = destream.open(fh.name)
            proc2 = archive2.p
            thread2 = archive2.t
            archive2 = None
            self.assertIsNotNone(proc2.poll())
            self.assertFalse(thread2.is_alive())
