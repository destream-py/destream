import re
import magic

from . import ArchiveFile


def determine_mime(f):
    pos = f.tell()
    mime = magic.from_buffer(f.read(1024), mime=True)
    f.seek(pos)
    return mime

__mime2obj__ = [
    (re.compile("^application/x-gzip$"), re.compile("\.gz$"), 'gzip', 'Gunzip'),
    (re.compile("^application/x-lzma$"), re.compile("\.lzma$"), 'lzma', 'Unlzma'),
    (re.compile("^application/x-tar$"), re.compile("\.tar$"), 'tar', 'Untar'),
]

def open(filename=None, fileobj=None):
    res_obj = ArchiveFile(filename, fileobj)
    for i in range(10):
        mime = determine_mime(res_obj)
        for re_mime, re_ext, module, obj in __mime2obj__:
            module = "%s.%s" % (__package__, module)
            if re_mime.search(mime) or \
               re_ext.search(res_obj.realname):
                res_obj = getattr(
                    __import__(module, globals(), locals(), [obj], -1),
                    obj)(res_obj, re_ext.sub('', res_obj.realname))
                break
        else:
            return res_obj
    raise Exception("More than 10 pipes or infinite loop detected")
