from StreamDecompressor import ExternalPipe

__all__ = ['Gunzip']


class Gunzip(ExternalPipe):
    __mimes__ = [
        'application/x-gzip',
        'application/gzip',
    ]
    __extensions__ = ['gz']
    __command__ = ['gunzip']
    __compression__ = 'gzip'

    @classmethod
    def __guess__(cls, mime, name, fileobj):
        if mime not in cls.__mimes__:
            raise ValueError("not a gzip compression")
        lowered = name.lower()
        if lowered.endswith('.gz'):
            realname = name[:-3]
        elif lowered.endswith('-gz'):
            realname = name[:-3]
        elif lowered.endswith('.z'):
            realname = name[:-2]
        elif lowered.endswith('-z'):
            realname = name[:-2]
        elif lowered.endswith('_z'):
            realname = name[:-2]
        elif lowered.endswith('.tgz') or lowered.endswith('.taz'):
            realname = name[:-4] + '.tar'
        else:
            realname = name
        return realname
