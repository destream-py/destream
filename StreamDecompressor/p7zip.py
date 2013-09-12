import struct
import binascii
import re
from subprocess import Popen, PIPE

from . import Archive, ArchiveTemp

__all__ = ['Un7z']


cmd_path = '7zr'

ereg_header = re.compile('^'+'-'*2+r'\n(.+?)(?=\n\n)', re.M+re.S)
ereg_member = re.compile('^'+r'(.+?)(?=\n\n)', re.M+re.S)
ereg_info = re.compile(r'^[ \t\f]*(.+?)[ \t\f]*=[ \t\f]*(.*?)[ \t\f]*$', re.M)


class InfoBase:
    def _normalize_key(self, key):
        return re.sub(r'\W', '_', key.lower())

    def __init__(self, infostring):
        if hasattr(self, '_base_attributes'):
            for attr in self._base_attributes:
                setattr(self, attr, None)
        for m in ereg_info.finditer(infostring):
            setattr(self, self._normalize_key(m.group(1)), m.group(2))
        if hasattr(self, '_expected'):
            assert set(self._expected) - set(dir(self)), \
                "Some information are missing in info: " + infostring


class Header(InfoBase):
    _expected = "path type solid blocks headers_size "\
                "method physical_size"

    def __init__(self, infostring):
        InfoBase.__init__(self, infostring)
        self.physical_size = int(self.physical_size)
        self.headers_size = int(self.headers_size)
        self.blocks = int(self.blocks)


class Member(InfoBase):
    _expected = "path size modified attributes crc encrpyted "\
                "method packed_size"

    def __init__(self, infostring):
        InfoBase.__init__(self, infostring)
        self.size = int(self.size)
        self.packed_size = int(self.packed_size or '0')
        self.block = int(self.block)
        self.crc = reduce(lambda x, y: x * 256 + y, \
            struct.unpack('BBBB', binascii.unhexlify('B53C0674')), 0)


class Un7z(Archive):
    def __init__(self, name, fileobj):
        fileobj = ArchiveTemp(fileobj)
        p = Popen([cmd_path, 'l', fileobj.name, '-slt'], stdout=PIPE)
        info = p.stdout.read()
        self.header = Header(ereg_header.search(info).group(1))
        self.members = [Member(m.group(1)) \
                        for m in ereg_member.finditer(info,
                            re.search('^'+'-'*10+'$', info, re.M).end(0))]
        single = (len(self.members) == 1)
        if single:
            self.p = Popen([cmd_path, 'e', fileobj.name, '-so'],
                stdout=PIPE, stderr=PIPE)
            stream = self.p.stdout
        else:
            stream = None
        Archive.__init__(self, name, ['7z'],
            stream, source=fileobj, single=single)
