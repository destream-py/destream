from destream import ExternalPipe

__all__ = ['Gunzip']


class Gunzip(ExternalPipe):
    _mimes = [
        'application/x-gzip',
        'application/gzip',
    ]
    _extensions = ['gz']
    _command = ['gunzip']
    _compression = 'gzip'

    @classmethod
    def _guess(cls, mime, name, fileobj):
        if mime not in cls._mimes:
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
