import struct
import binascii
import re
from subprocess import Popen, PIPE

from StreamDecompressor import ArchivePack, ArchiveTemp, ExternalPipe

__all__ = ['Un7z']


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
            assert set(self._expected) - set(dir(self)) == set(), \
                "Some information are missing in info:\n" + infostring


class Header(InfoBase):
    _expected = "path type solid blocks headers_size "\
                "method physical_size".split()

    def __init__(self, infostring):
        InfoBase.__init__(self, infostring)
        self.physical_size = int(self.physical_size)
        self.headers_size = int(self.headers_size)
        self.blocks = int(self.blocks)


class Member(InfoBase):
    _expected = "path size modified attributes crc encrypted "\
                "method packed_size".split()

    def __init__(self, infostring):
        InfoBase.__init__(self, infostring)
        self.size = int(self.size)
        self.packed_size = int(self.packed_size or '0')
        self.block = int(self.block or '0')
        self.crc = reduce(lambda x, y: x * 256 + y, \
            struct.unpack('BBBB', binascii.unhexlify('B53C0674')), 0)


class Un7z(ArchivePack):
    __mimes__ = ['application/x-7z-compressed']
    __extensions__ = ['7z']
    __command__ = ['7zr']
    __compression__ = '7z'

    @classmethod
    def __checkavailability__(cls):
        return ExternalPipe.__checkavailability__.im_func(cls)

    def __init__(self, name, fileobj):
        self.fileobj = ArchiveTemp(fileobj)
        p = Popen(self.__command__ + ['l', self.fileobj.name, '-slt'],
                  stdout=PIPE)
        info = p.stdout.read()
        self.header = Header(ereg_header.search(info).group(1))
        self._members = [Member(m.group(1)) \
                        for m in ereg_member.finditer(info,
                            re.search('^'+'-'*10+'$', info, re.M).end(0))]
        if len(self._members) == 1:
            self.p = Popen(self.__command__ + ['e', self.fileobj.name, '-so'],
                           stdout=PIPE, stderr=PIPE)
            self.p.stderr.close()
            stream = self.p.stdout
        else:
            stream = self.fileobj
            stream.seek(0)
        ArchivePack.__init__(self, name, stream, source=fileobj)

    def members(self):
        return self._members

    def open(self, member, stream=True):
        p = Popen(self.__command__ +
            ['e', self.fileobj.name, '-so',
            (member.path if isinstance(member, Member) else member)],
            stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        if stream:
            return p.stdout
        else:
            temp = ArchiveTemp(p.stdout)
            ret = p.wait()
            if ret != 0:
                raise Exception("Process returned with value=%d" % ret)
            return temp

    def extract(self, member, path):
        p = Popen(self.__command__ +
            ['e', self.fileobj.name, '-y', '-o'+path,
            (member.path if isinstance(member, Member) else member)],
            stdout=PIPE)
        p.stdout.close()
        ret = p.wait()
        if ret != 0:
            raise Exception("Process returned with value=%d" % ret)

    def extractall(self, path, members=[]):
        p = Popen(self.__command__ +
            ['x', self.fileobj.name, '-y', '-o'+path] +
            [(m.path if isinstance(m, Member) else m) for m in members],
            stdout=PIPE)
        p.stdout.close()
        ret = p.wait()
        if ret != 0:
            raise Exception("Process returned with value=%d" % ret)
