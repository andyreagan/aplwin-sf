"""
aplwin-sf: Read APL+Win component files (.sf) from Python.

APL+Win stores source code and data in a proprietary binary format called
"component files" (extension .sf). This library parses them and decodes
APL+Win's character encoding to Unicode, producing readable UTF-8 text.

Typical usage::

    from aplwin_sf import read_functions

    for fn in read_functions("myfuncs.sf"):
        print(fn.name, fn.text[:80])

Or from the command line::

    aplwin-sf myfuncs.sf             # print to stdout
    aplwin-sf /path/to/dir -o out/   # extract all .sf files to a directory
"""

from .encoding import APL_MAP, decode
from .parser import read_file, read_functions, Function, ComponentFile

__all__ = [
    "APL_MAP",
    "decode",
    "read_file",
    "read_functions",
    "Function",
    "ComponentFile",
]

__version__ = "0.1.0"
