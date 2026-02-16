"""Build synthetic .sf test fixtures from scratch.

Run this script directly to regenerate the fixtures/ directory.
No proprietary data is used — all content is fabricated.
"""

from __future__ import annotations

import struct
from pathlib import Path


def _encode_apl(text: str) -> bytes:
    """Encode a Unicode APL string to APL+Win font bytes.

    This is the *inverse* of aplwin_sf.decode — used only for building
    test fixtures.
    """
    # Build reverse map (Unicode char → byte)
    from aplwin_sf.encoding import APL_MAP

    reverse: dict[str, int] = {}
    for byte_val, char in APL_MAP.items():
        if char == "\n":
            continue  # handle separately
        # Don't let APL_MAP entries shadow standard ASCII characters.
        # A character that has a standard ASCII code point (0x20-0x7E)
        # should encode to that code point, not to a high-byte alias.
        if len(char) == 1 and 0x20 <= ord(char) <= 0x7E:
            continue
        reverse.setdefault(char, byte_val)

    parts = bytearray()
    for ch in text:
        if ch == "\n":
            parts.append(0x0D)
        elif ch in reverse:
            parts.append(reverse[ch])
        elif 0x20 <= ord(ch) <= 0x7E:
            parts.append(ord(ch))
        elif ch == "\t":
            parts.append(0x09)
        else:
            parts.append(ord(ch) & 0xFF)
    return bytes(parts)


def _make_sub_object(fn_text_bytes: bytes) -> bytes:
    """Wrap encoded function text in a sub-object header."""
    text_len = len(fn_text_bytes)
    padding = (4 - (text_len % 4)) % 4
    total_size = 20 + text_len + padding
    header = struct.pack("<IIIII", total_size, 1, 0x01002020, text_len, text_len)
    return header + fn_text_bytes + (b"\x00" * padding)


def _make_sf(sub_objects: list[bytes]) -> bytes:
    """Build a complete .sf file from a list of sub-object byte blobs.

    Places all sub-objects sequentially inside one component starting
    at the standard offset 1056 (0x420), preceded by a valid file
    header and component directory.
    """
    comp_data = b"".join(sub_objects)
    comp_offset = 1056
    comp_length = len(comp_data)
    file_size = comp_offset + comp_length

    # 88-byte file header
    header = struct.pack(
        "<IIIIIII",
        1,  # version
        2,  # next_component_number
        1,
        0x56AB558E,  # timestamp (arbitrary)
        1,
        0x56AB558E,
        file_size,
    )
    header += b"\x00" * (88 - len(header))

    # Component directory: one entry + terminator
    directory = struct.pack("<II", comp_offset, comp_length)
    directory += struct.pack("<II", 0, 0)  # end marker

    # Pad to comp_offset
    padding = comp_offset - len(header) - len(directory)
    assert padding >= 0

    return header + directory + (b"\x00" * padding) + comp_data


def make_simple() -> bytes:
    """One function: R←ADD A;B."""
    src = "    ∇ R←ADD A;B\n[1]   B←1\n[2]   R←A+B\n    ∇\n"
    return _make_sf([_make_sub_object(_encode_apl(src))])


def make_multi() -> bytes:
    """Three functions in one file, exercising various APL symbols."""
    fn1 = (
        "    ∇ R←N TAKE V;⎕IO\n"
        "[1]   ⎕IO←1\n"
        "[2]   R←N↑V\n"
        "    ∇\n"
    )
    fn2 = (
        "    ∇ R←IOTA N\n"
        "[1]   R←⍳N\n"
        "    ∇\n"
    )
    fn3 = (
        "    ∇ R←A PLUS B\n"
        "[1]   ⍝ Add two values\n"
        "[2]   R←A+B\n"
        "    ∇\n"
    )
    blobs = [_make_sub_object(_encode_apl(f)) for f in [fn1, fn2, fn3]]
    return _make_sf(blobs)


def make_apl_symbols() -> bytes:
    """One function that exercises many APL symbols."""
    src = (
        "    ∇ R←DEMO X;⎕IO;M;V\n"
        "[1]   ⎕IO←0\n"
        "[2]   ⍝ Shape, iota, rho, floor, ceiling\n"
        "[3]   M←3 4⍴⍳12\n"
        "[4]   V←⌊0.5+⌈÷2\n"
        "[5]   R←(⍴M)↑(⍴M)↓V\n"
        "[6]   →(R≡⍬)/0\n"
        "[7]   R←∊⊂R\n"
        "[8]   R←R⍪⍉M\n"
        "    ∇\n"
    )
    return _make_sf([_make_sub_object(_encode_apl(src))])


def make_data_and_functions() -> bytes:
    """Mix of non-function binary data and function text sub-objects.

    Simulates a real .sf file where function text is interleaved with
    data arrays (rate tables, etc.).
    """
    # A blob of fake "data" — NOT a function (no marker)
    fake_data = struct.pack("<III", 64, 1, 0x02000000) + b"\x00" * 52

    fn = (
        "    ∇ R←DOUBLE N\n"
        "[1]   R←2×N\n"
        "    ∇\n"
    )
    fn_blob = _make_sub_object(_encode_apl(fn))

    # More fake data
    fake_data2 = struct.pack("<III", 48, 1, 0x03000000) + b"\x00" * 36

    fn2 = (
        "    ∇ R←HALF N\n"
        "[1]   R←N÷2\n"
        "    ∇\n"
    )
    fn2_blob = _make_sub_object(_encode_apl(fn2))

    return _make_sf([fake_data, fn_blob, fake_data2, fn2_blob])


def make_empty() -> bytes:
    """An .sf file with no function text — only data."""
    fake_data = struct.pack("<III", 64, 1, 0x02000000) + b"\x00" * 52
    return _make_sf([fake_data])


def make_high_minus() -> bytes:
    """Function using ¯ (high minus / macron / overbar)."""
    src = (
        "    ∇ R←LASTROW M\n"
        "[1]   R←(¯1↑⍴M)↑M\n"
        "    ∇\n"
    )
    return _make_sf([_make_sub_object(_encode_apl(src))])


FIXTURES = {
    "simple.sf": make_simple,
    "multi.sf": make_multi,
    "symbols.sf": make_apl_symbols,
    "mixed.sf": make_data_and_functions,
    "empty.sf": make_empty,
    "high_minus.sf": make_high_minus,
}


def build_all(dest: Path | str = Path(__file__).resolve().parent.parent / "fixtures"):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for name, builder in FIXTURES.items():
        (dest / name).write_bytes(builder())
        print(f"  {name}: {(dest / name).stat().st_size} bytes")


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    build_all()
