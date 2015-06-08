import struct
import binascii
import re
from functools import reduce
from subprocess import check_output, Popen, PIPE, CalledProcessError

from destream import ArchivePack, ArchiveTemp, ExternalPipe

__all__ = ['Un7z']


ereg_header = re.compile('^'+r'--+\n(.+?)(?=\n\n)', re.M+re.S)
ereg_member = re.compile('^'+r'(.+?)(?=\n\n)', re.M+re.S)


def parse_hunk(hunk):
    info = {}
    for m in re.finditer(
            r'^[ \t\f]*(.+?)[ \t\f]*=[ \t\f]*(.*?)[ \t\f]*$',
            hunk, flags=re.M):
        key = re.sub(r'\W', '_', m.group(1).lower())
        info[key] = m.group(2)
    return info


class Header(object):
    def __init__(self, hunk):
        info = parse_hunk(hunk)
        info['physical_size'] = int(info['physical_size'])
        info['headers_size'] = int(info['headers_size'])
        info['blocks'] = int(info['blocks'])
        self.__dict__.update(info)


class Member(object):
    def __init__(self, hunk):
        info = parse_hunk(hunk)
        info['filename'] = info['path']
        info['size'] = int(info['size'])
        info['packed_size'] = int(info['packed_size'] or '0')
        info['block'] = int(info['block'] or '0')
        if info['crc']:
            info['crc'] = reduce(lambda x, y: x * 256 + y, \
                struct.unpack('BBBB', binascii.unhexlify(info['crc'])), 0)
        self.__dict__.update(info)

    def isfile(self):
        return self.attributes[0] != 'D'

    def isdir(self):
        return self.attributes[0] == 'D'


class Un7z(ArchivePack):
    _mimes = ['application/x-7z-compressed']
    _extensions = ['7z']
    _command = ['7zr']
    _compression = '7z'

    @classmethod
    def _check_availability(cls):
        return ExternalPipe._check_availability.__func__(cls)

    def __init__(self, name, fileobj):
        self.fileobj = ArchiveTemp(fileobj)
        info = check_output(self._command +
                            ['l', self.fileobj.name, '-slt']).decode()
        self.header = Header(ereg_header.search(info).group(1))
        self._members = [Member(m.group(1)) \
                        for m in ereg_member.finditer(info,
                            re.search('^'+'-'*10+'$', info, re.M).end(0))]
        self._stream = (len(self._members) == 1)
        if self._stream:
            stream = self.open(self._members[0])
            stream_name = self._members[0].filename
            self._compression += ':' + stream_name
        else:
            stream_name = name
            stream = self.fileobj
            stream.seek(0)
        ArchivePack.__init__(self, stream_name, stream, source=fileobj)

    def members(self):
        return self._members

    def open(self, member):
        p = Popen(self._command +
            ['e', self.fileobj.name, '-so',
            (member.filename if isinstance(member, Member) else member)],
            stdout=PIPE, stderr=PIPE)
        if self._stream:
            self._p = p
            return p.stdout
        else:
            try:
                temp = ArchiveTemp(p.stdout)
                retcode = p.wait()
                if retcode:
                    raise CalledProcessError(
                        retcode, self._command, output=p.stderr.read())
            finally:
                p.stdout.close()
                p.stderr.close()
            return temp

    @property
    def closed(self):
        if self._stream:
            return self._p.stdout.closed
        else:
            return self.fileobj.closed

    def close(self):
        if self._stream:
            if not self.closed:
                self._p.stdout.close()
                self._p.stderr.close()
                self._p.wait()
        else:
            self.fileobj.close()

    def extract(self, member, path):
        p = Popen(self._command +
            ['x', self.fileobj.name, '-y', '-o'+path,
            (member.filename if isinstance(member, Member) else member)],
            stdout=PIPE)
        try:
            retcode = p.wait()
            if retcode:
                raise CalledProcessError(
                    retcode, self._command, output=p.stdout.read())
        finally:
            p.stdout.close()

    def extractall(self, path, members=[]):
        p = Popen(self._command +
            ['x', self.fileobj.name, '-y', '-o'+path] +
            [(m.filename if isinstance(m, Member) else m) for m in members],
            stdout=PIPE)
        try:
            retcode = p.wait()
            if retcode:
                raise CalledProcessError(
                    retcode, self._command, output=p.stdout.read())
        finally:
            p.stdout.close()
