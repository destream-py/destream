import struct
import binascii
import re
from subprocess import check_output, Popen, PIPE, CalledProcessError
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
    __command__ = ['rar']
    __compression__ = 'rar'
    # NOTE:
    #   https://en.wikipedia.org/wiki/Unrar
    #   Unrar is the name of two different programs, we should prefer rar by
    #   default to make sure to use the most recent and compatible version if
    #   available.
    __fallbackcommands__ = ['unrar']

    @classmethod
    def __checkavailability__(cls):
        ExternalPipe.__checkavailability__.im_func(cls)
        output = check_output(cls.__command__)
        matches = re.search("(?:UN)?RAR (\d+\.\d+)", output)
        assert matches, "%s: can not determine version" \
                        % cls.__command__[0]
        cls.version = tuple(Version(matches.group(1)).version)
        # NOTE: the parameter vta is available from version 5
        assert cls.version >= (5, 0), "%s: incompatible version %s" \
                                      % (cls.__command__[0], cls.version)

    def __init__(self, name, fileobj):
        self.fileobj = ArchiveTemp(fileobj)
        output = check_output(self.__command__ + ['vta', self.fileobj.name])
        hunks = iter(output.split("\n\n"))
        self.information = hunks.next().strip()
        self.header = Header(hunks.next())
        self._members = [m for m in (Member(h) for h in hunks)]
        self._stream = (len(self._members) == 1)
        if self._stream:
            stream = self.open(self._members[0])
            stream_name = self._members[0].filename
            self.__compression__ += ':' + stream_name
        else:
            stream_name = name
            stream = self.fileobj
            stream.seek(0)
        ArchivePack.__init__(self, stream_name, stream, source=fileobj)

    def members(self):
        return self._members

    def open(self, member):
        p = Popen(self.__command__ +
            ['p', '-ierr', self.fileobj.name,
             (member.filename if isinstance(member, Member) else member)],
            stdout=PIPE, stderr=PIPE)
        if self._stream:
            self._p = p
            return p.stdout
        else:
            temp = ArchiveTemp(p.stdout)
            retcode = p.wait()
            if retcode:
                raise CalledProcessError(
                    retcode, self.__command__, output=p.stderr.read())
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
                self._p.wait()
        else:
            self.fileobj.close()

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
