"""
Parser for APL+Win component files (.sf).

APL+Win component files store APL objects (functions, variables, arrays)
in a binary format.  This module extracts function source code by scanning
for the function-text marker and decoding the surrounding structure.

Binary layout of a function-text sub-object::

    offset  size  description
    ──────  ────  ─────────────────────────────────
    +0      4     total_size  (header + text + pad)
    +4      4     const       (always 1)
    +8      4     type_flags
    +12     4     text_length
    +16     4     text_length (repeated)
    +20     N     APL text in font encoding
    +20+N   0-3   zero padding to 4-byte boundary

The APL text begins with ``"    ∇ "`` (four spaces, del, space) followed
by the function header, then CR-separated numbered lines ``[1]``,
``[2]``, etc., ending with ``"    ∇"`` and a final CR.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from .encoding import decode

__all__ = ["Function", "ComponentFile", "read_file", "read_functions"]

# Four spaces + ∇ (0xEC) + space — marks the start of function text
# at byte offset +20 inside each sub-object.
_FUNCTION_MARKER = b"\x20\x20\x20\x20\xEC\x20"


def _u32(data: bytes | bytearray, offset: int) -> int:
    """Read a little-endian uint32."""
    return struct.unpack_from("<I", data, offset)[0]


@dataclass(frozen=True)
class Function:
    """A single APL function extracted from a component file.

    Attributes
    ----------
    name : str
        Function name parsed from the header line.
    text : str
        Complete function source, including the ``∇`` delimiters and
        numbered lines, as a Unicode string.
    offset : int
        Byte offset of the function-text sub-object header within the
        file.  Useful for diagnostics.
    raw : bytes
        The undecoded bytes of the function text (everything between
        the sub-object header and the end of text_length).
    """

    name: str
    text: str
    offset: int
    raw: bytes


@dataclass(frozen=True)
class ComponentFile:
    """Result of reading a ``.sf`` file.

    Attributes
    ----------
    path : str
        Filesystem path that was read (or ``"<bytes>"`` if read from
        raw data).
    functions : list[Function]
        Extracted functions, in file order.
    size : int
        Total size of the input data in bytes.
    """

    path: str
    functions: list[Function]
    size: int


def _parse_function_name(header_line: str) -> str:
    """Extract the function name from a ∇-header line.

    APL function header forms::

        ∇ NAME                     niladic
        ∇ NAME RARG                monadic
        ∇ LARG NAME RARG           dyadic
        ∇ RES←NAME                 niladic with result
        ∇ RES←NAME RARG            monadic with result
        ∇ RES←LARG NAME RARG       dyadic with result

    Any form may have ``;locals`` appended.
    """
    line = header_line.strip()
    if line.startswith("∇"):
        line = line[1:].strip()

    # Strip locals
    line = line.split(";")[0].strip()

    if "←" in line:
        line = line.split("←", 1)[1].strip()

    words = line.split()
    if len(words) >= 3:
        # dyadic: LARG NAME RARG — name is the second word
        return words[1]
    elif len(words) >= 1:
        # monadic or niladic: NAME [RARG]
        return words[0]
    return ""


def read_functions(source: str | Path | bytes | bytearray) -> list[Function]:
    """Extract APL functions from a ``.sf`` file or raw bytes.

    This is the main entry point.  Pass a filename, :class:`~pathlib.Path`,
    or raw ``bytes`` and get back a list of :class:`Function` objects.

    Parameters
    ----------
    source : str, Path, bytes, or bytearray
        Path to a ``.sf`` file, or the raw file contents.

    Returns
    -------
    list[Function]
        Functions found in file order.  Empty list if no functions.

    Examples
    --------
    >>> fns = read_functions("myfuncs.sf")
    >>> fns[0].name
    'ADD'
    >>> print(fns[0].text[:20])
    ∇ R←ADD N
    """
    return read_file(source).functions


def read_file(source: str | Path | bytes | bytearray) -> ComponentFile:
    """Read a ``.sf`` file and return a :class:`ComponentFile`.

    Parameters
    ----------
    source : str, Path, bytes, or bytearray
        Path to a ``.sf`` file, or the raw file contents.

    Returns
    -------
    ComponentFile
    """
    if isinstance(source, (bytes, bytearray)):
        data = bytes(source)
        path = "<bytes>"
    else:
        p = Path(source)
        data = p.read_bytes()
        path = str(p)

    functions: list[Function] = []
    idx = 0

    while idx < len(data):
        pos = data.find(_FUNCTION_MARKER, idx)
        if pos < 0:
            break

        header_off = pos - 20
        if header_off < 0:
            idx = pos + 6
            continue

        # Read and validate the sub-object header
        try:
            _obj_size = _u32(data, header_off)
            const = _u32(data, header_off + 4)
            text_len = _u32(data, header_off + 12)
            text_len2 = _u32(data, header_off + 16)
        except struct.error:
            idx = pos + 6
            continue

        if const != 1 or text_len != text_len2:
            idx = pos + 6
            continue
        if text_len <= 0 or text_len > 10_000_000:
            idx = pos + 6
            continue
        if pos + text_len > len(data):
            idx = pos + 6
            continue

        raw_text = data[pos : pos + text_len]
        text = decode(raw_text)
        name = _parse_function_name(text.split("\n")[0]) or f"_unnamed_{len(functions)}"

        functions.append(
            Function(name=name, text=text.strip(), offset=header_off, raw=raw_text)
        )

        idx = pos + text_len

    return ComponentFile(path=path, functions=functions, size=len(data))
