import sys
import inspect

from StreamDecompressor import archive

from gzip import *
from bz2 import *
from lzma import *
from p7zip import *
from tar import *
from xz import *
from zip import *
from rar import *

builtin_decompressors = [
    (0, symbol)
    for name, symbol
    in inspect.getmembers(sys.modules[__name__], inspect.isclass)
    if issubclass(symbol, archive.Archive)
]
