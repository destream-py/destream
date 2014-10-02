import sys
import inspect

from StreamDecompressor import archive

from StreamDecompressor.decompressors.gzip import *
from StreamDecompressor.decompressors.bzip2 import *
from StreamDecompressor.decompressors.lzma import *
from StreamDecompressor.decompressors.p7zip import *
from StreamDecompressor.decompressors.tar import *
from StreamDecompressor.decompressors.xz import *
from StreamDecompressor.decompressors.zip import *
from StreamDecompressor.decompressors.rar import *

builtin_decompressors = [
    (0, symbol)
    for name, symbol
    in inspect.getmembers(sys.modules[__name__], inspect.isclass)
    if issubclass(symbol, archive.Archive)
]
