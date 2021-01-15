from io import BytesIO
from pathlib import Path

import pytest

from destream import Archive, ArchiveFile, ArchiveTemp, ExternalPipe


class BaseNameExample(Archive):
    _extensions = ["ext1", "ext2"]
    _mimes = ["mime1", "mime2"]


def test_archive_guess_basename():
    fileobj = BytesIO(b"")
    assert "xxx" == BaseNameExample._guess("mime2", "xxx", fileobj)
    assert "xxx" == BaseNameExample._guess("mime1", "xxx.ext2", fileobj)
    assert "xxx" == BaseNameExample._guess("mime2", "xxx.ext1", fileobj)
    with pytest.raises(ValueError):
        assert BaseNameExample._guess("xxx", "xxx.ext1", fileobj)


def test_archivefile_passing_file_object(tmp_path):
    text = b"Hello World!\n"
    path = tmp_path / "testfile"
    with path.open("w+b") as fileobj:
        fileobj.write(text)
        fileobj.flush()
        archive = ArchiveFile(fileobj=fileobj)
        assert archive.fileno() == fileobj.fileno()
        assert archive.name == fileobj.name
        archive.seek(0)
        assert archive.read() == text


def test_archivefile_passing_file_name(tmp_path):
    text = b"Hello World!\n"
    filename = tmp_path / "testfile"
    with filename.open("w+b") as fileobj:
        fileobj.write(text)
    archive = ArchiveFile(name=filename)
    assert archive.name == filename
    assert archive.read() == text


def test_archivefile_closefd():
    fileobj = BytesIO()
    archive = ArchiveFile(fileobj=fileobj, closefd=False)
    archive.close()
    assert not fileobj.closed
    archive = ArchiveFile(fileobj=fileobj, closefd=True)
    archive.close()
    assert fileobj.closed


class CatsEye(ExternalPipe):
    _command = ["cat"]
    _compression = "cat"
    _unique_instance = True


def test_externalpipe_check_output():
    text = b"Hello World\n"
    filename = "<pipe_test>"
    fileobj = BytesIO(text)
    with CatsEye(filename, fileobj) as pipe:
        with pytest.raises(ValueError):
            CatsEye._guess("", filename, pipe)
        assert pipe.compressions == ["cat"]
        assert pipe._decompressors == [CatsEye]
        assert pipe.realname == filename
        assert pipe.read() == text
        assert pipe.read() == b""


def test_create_temp_archive_from_externalpipe():
    text = b"Hello World\n"
    filename = "some_file"
    fileobj = BytesIO(text)
    with CatsEye(filename, fileobj) as pipe:
        temp = ArchiveTemp(pipe)
        assert pipe.read() == b""
        assert (
            Path(filename).resolve().parent == Path(temp.name).resolve().parent
        )
        assert temp.read() == text
