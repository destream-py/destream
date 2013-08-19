import re
import magic

from . import ArchiveFile


def determine_mime(archive):
    return magic.from_buffer(archive.peek(1024), mime=True)

__mime2obj__ = [
    (re.compile("^application/x-gzip$"), re.compile("\.gz$"), 'gzip', 'Gunzip'),
    (re.compile("^application/x-lzma$"), re.compile("\.lzma$"), 'lzma', 'Unlzma'),
    (re.compile("^application/x-7z-compressed$"), re.compile("\.7z$"), 'p7zip', 'Un7z'),
    (re.compile("^application/x-tar$"), re.compile("\.tar$"), 'tar', 'Untar'),
    (re.compile("^application/zip$"), re.compile("\.zip$"), 'zip', 'Unzip'),
]

def open(name=None, fileobj=None):
    res_obj = ArchiveFile(fileobj, name)
    res_obj.seek(0)
    for i in range(10):
        mime = determine_mime(res_obj)
        for re_mime, re_ext, module, obj in __mime2obj__:
            module = "%s.%s" % (__package__, module)
            if re_mime.search(mime) or \
               re_ext.search(res_obj.realname):
                res_obj = getattr(
                    __import__(module, globals(), locals(), [obj], -1),
                    obj)(re_ext.sub('', res_obj.realname), res_obj)
                break
        else:
            return res_obj
    raise Exception("More than 10 pipes or infinite loop detected")
