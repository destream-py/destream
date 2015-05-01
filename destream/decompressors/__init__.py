import sys
import inspect

from destream import archive

from destream.decompressors.gzip import *
from destream.decompressors.bzip2 import *
from destream.decompressors.lzma import *
from destream.decompressors.p7zip import *
from destream.decompressors.tar import *
from destream.decompressors.xz import *
from destream.decompressors.zip import *
from destream.decompressors.rar import *

builtin_decompressors = [
    (0, symbol)
    for name, symbol
    in inspect.getmembers(sys.modules[__name__], inspect.isclass)
    if issubclass(symbol, archive.Archive)
]
