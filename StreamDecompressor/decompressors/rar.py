import struct
import binascii
import re
from subprocess import Popen, PIPE, CalledProcessError
from distutils.version import LooseVersion as Version

from StreamDecompressor import ArchivePack, ArchiveTemp, ExternalPipe

__all__ = ['Unrar']


def parse_hunk(hunk):
    info = {}
    for m in re.finditer(
            r'^[ \t\f]*(.+?)[ \t\f]*:[ \t\f]*(.*?)[ \t\f]*$',
            hunk, flags=re.M):
        key = re.sub(r'\W', '_', m.group(1).lower())
        info[key] = m.group(2)
    if info.get('service', '') == 'EOF':
        raise StopIteration()
    return info


class Header(object):
    def __init__(self, hunk):
        self.__dict__.update(parse_hunk(hunk))
        assert 'RAR' in self.details, \
            "Maybe not a RAR file:%s\n" % self.details


class Member(object):
    def __init__(self, hunk):
        info = parse_hunk(hunk)
        info['filename'] = info.pop('name')
        info['size'] = int(info.get('size', 0))
        info['packed_size'] = int(info.get('packed_size', 0))
        info['ratio'] = float(info.get('ratio', '0%')[:-1]) / 100.0
        info['crc32'] = reduce(lambda x, y: x * 256 + y, \
            struct.unpack('BBBB', binascii.unhexlify(info['crc32'])), 0)
        self.__dict__.update(info)

    def isfile(self):
        return self.type == 'File'

    def isdir(self):
        return self.type == 'Directory'

class Unrar(ArchivePack):
    __mimes__ = ['application/x-rar']
    __extensions__ = ['rar']
    __command__ = ['unrar']
    __compression__ = 'rar'
    __fallbackcommands__ = ['rar']

    @classmethod
    def __checkavailability__(cls):
        return ExternalPipe.__checkavailability__.im_func(cls)

    def __init__(self, name, fileobj):
        self.fileobj = ArchiveTemp(fileobj)
        p = Popen(self.__command__ + ['vta', self.fileobj.name],
                  stdout=PIPE)
        hunks = iter(p.stdout.read().split("\n\n"))
        self.information = hunks.next().strip()
        matches = re.match("(\S+| (?! ))+", self.information)
        assert matches, "can not parse rar information header"
        self.version = tuple(
            Version(matches.group(0).replace(' ', '.'))\
            .version[1:])
        # NOTE: I only know it works with version 5 but not with version 3
        # it could works with version 4...
        assert self.version >= (4,), \
            "This version of %s (%s) is probably not compatible" \
            % (self.__command__[0], self.version)
        self.header = Header(hunks.next())
        self._members = [m for m in (Member(h) for h in hunks)]
        if len(self._members) == 1:
            stream = self.open(self._members[0], stream=True)
            stream_name = self._members[0].filename
        else:
            stream_name = name
            stream = self.fileobj
            stream.seek(0)
        ArchivePack.__init__(self, stream_name, stream, source=fileobj)

    def members(self):
        return self._members

    def open(self, member, stream=True):
        p = Popen(self.__command__ +
            ['p', '-ierr', self.fileobj.name,
             (member.filename if isinstance(member, Member) else member)],
            stdout=PIPE, stderr=PIPE)
        if stream:
            return p.stdout
        else:
            temp = ArchiveTemp(p.stdout)
            retcode = p.wait()
            if retcode:
                raise CalledProcessError(
                    retcode, self.__command__, output=p.stderr.read())
            return temp

    def extract(self, member, path):
        p = Popen(self.__command__ +
            ['x', self.fileobj.name,
             (member.filename if isinstance(member, Member) else member),
             path], stdout=PIPE)
        retcode = p.wait()
        if retcode:
            raise CalledProcessError(
                retcode, self.__command__, output=p.stdout.read())

    def extractall(self, path, members=[]):
        p = Popen(self.__command__ +
            ['x', self.fileobj.name] +
            [(m.filename if isinstance(m, Member) else m) for m in members] +
            [path], stdout=PIPE)
        retcode = p.wait()
        if retcode:
            raise CalledProcessError(
                retcode, self.__command__, output=p.stdout.read())
