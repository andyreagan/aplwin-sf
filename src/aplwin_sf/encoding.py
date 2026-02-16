"""
APL+Win character encoding: byte → Unicode mapping.

APL+Win uses a custom single-byte encoding based on Code Page 437 with
APL symbol overlays. Positions 0x20–0x7E are standard ASCII. Positions
in the control-character range (0x00–0x1F) and the high range (0x80–0xFF)
are mapped to APL symbols and accented Latin characters.

This mapping was reverse-engineered from function text stored in .sf
component files and cross-referenced against the ∆AV table published
in Dyalog's aplwincfs project (https://github.com/Dyalog/aplwincfs).

Note: The Dyalog ∆AV maps ⎕AV *indices* (logical positions in APL's
atomic vector) to Unicode. The .sf file encoding maps raw *byte values*
(the font/codepage encoding) to Unicode. These are different mappings—
the same byte value maps to different characters depending on context.
Both are useful; this module implements the file-encoding mapping.
"""

from __future__ import annotations

# fmt: off
APL_MAP: dict[int, str] = {
    # ── Control-character region: APL symbols ──────────────────────
    0x03: '⍷',   # find / epsilon underbar
    0x04: '∊',   # epsilon / membership
    0x05: '¨',   # dieresis / each
    0x06: '←',   # left arrow / assignment
    0x0B: '⊂',   # enclose / subset
    0x0D: '\n',  # CR → newline (line separator in function text)
    0x0E: '⊃',   # disclose / superset
    0x0F: '⍟',   # natural log / circle star
    0x13: '⍫',   # del tilde
    0x16: '⍬',   # zilde / empty numeric vector
    0x17: '⍵',   # omega / right argument
    0x18: '↑',   # take / mix
    0x19: '×',   # times
    0x1A: '→',   # branch / goto
    0x1C: '⊣',   # left tack
    0x1D: '⊢',   # right tack
    0x1E: '⍋',   # grade up
    0x1F: '⍒',   # grade down / rotate

    # ── 0x80–0x9F: APL symbols + accented Latin ───────────────────
    0x80: 'Ç',  0x81: 'ü',  0x82: 'é',  0x83: 'â',  0x84: 'ä',
    0x85: 'à',
    0x86: '⍴',   # rho / shape
    0x87: 'ç',  0x88: 'ê',  0x89: 'ë',  0x8A: 'è',
    0x8B: '⍕',   # format
    0x8C: '⍎',   # execute
    0x8D: '↓',   # drop
    0x8E: 'Ä',
    0x8F: '×',   # times (variant position)
    0x90: 'É',
    0x91: '⋄',   # diamond / statement separator
    0x92: '×',   # times (variant position)
    0x93: 'ô',  0x94: 'ö',
    0x95: '⎕',   # quad
    0x96: 'û',
    0x97: '⍞',   # quote quad
    0x98: '⌹',   # domino / quad divide
    0x99: 'Ö',  0x9A: 'Ü',  0x9B: '¢',  0x9C: '£',  0x9D: '¥',
    0x9E: '⍪',   # comma bar
    0x9F: '⍨',   # commute / selfie

    # ── 0xA0–0xAF: accented Latin + APL symbols ──────────────────
    0xA0: 'á',  0xA1: 'í',  0xA2: 'ó',  0xA3: 'ú',  0xA4: 'ñ',
    0xA5: 'Ñ',
    0xA6: '⍝',   # comment / lamp
    0xA7: '⍀',   # scan first axis
    0xA8: '¿',
    0xA9: '⌷',   # squad / index
    0xAA: 'õ',  0xAB: 'ø',  0xAC: 'ý',  0xAD: '¡',
    0xAE: '«',  0xAF: '»',

    # ── 0xB0–0xBF: box drawing ────────────────────────────────────
    0xB0: '─',  0xB1: '│',  0xB2: '┌',  0xB3: '┐',
    0xB4: '└',  0xB5: '┘',  0xB6: '├',  0xB7: '┤',
    0xB8: '┬',  0xB9: '┴',  0xBA: '┼',
    0xBB: '╭',  0xBC: '╮',  0xBD: '╯',  0xBE: '╰',
    0xBF: '…',

    # ── 0xC0–0xDF: Latin / math / symbols ─────────────────────────
    0xC0: 'À',  0xC1: 'Á',  0xC2: 'Â',  0xC3: 'Ã',  0xC4: '¶',
    0xC5: 'Å',  0xC6: 'Æ',  0xC7: 'ƒ',  0xC8: 'È',  0xC9: '™',
    0xCA: 'Ê',  0xCB: 'Ë',  0xCC: 'Ì',  0xCD: 'Í',  0xCE: 'Î',
    0xCF: 'Ï',
    0xD0: '©',  0xD1: '®',  0xD2: 'Ò',  0xD3: 'Ó',  0xD4: 'Ô',
    0xD5: 'Õ',  0xD6: '≈',  0xD7: '≊',  0xD8: 'Ø',  0xD9: 'Ù',
    0xDA: 'Ú',  0xDB: 'Û',  0xDC: '≅',  0xDD: 'Ý',  0xDE: '≣',
    0xDF: 'ÿ',

    # ── 0xE0–0xFF: core APL symbols ───────────────────────────────
    0xE0: '⍺',   # alpha / left argument
    0xE1: 'ß',   # sharp s (Latin, used in identifiers)
    0xE2: '⍳',   # iota / index generator
    0xE3: '⍤',   # rank / jot dieresis
    0xE4: '⊆',   # nest / partition
    0xE5: '⍱',   # nor
    0xE6: '⊥',   # decode / base
    0xE7: '⊤',   # encode / represent
    0xE8: '⌊',   # floor / minimum
    0xE9: '⊖',   # rotate first axis
    0xEA: '⍲',   # nand
    0xEB: '⌿',   # replicate first axis
    0xEC: '∇',   # del / nabla
    0xED: '⍉',   # transpose
    0xEE: '∊',   # epsilon / membership (variant position)
    0xEF: '¯',   # high minus / macron / overbar
    0xF0: '≡',   # match / depth
    0xF1: '⍙',   # delta underbar
    0xF2: '≥',   # greater than or equal
    0xF3: '≤',   # less than or equal
    0xF4: '⍕',   # format (variant position)
    0xF5: '⍎',   # execute (variant position)
    0xF6: '÷',   # divide
    0xF7: '„',   # double low-9 quotation mark
    0xF8: '∘',   # jot / compose
    0xF9: '○',   # circle / pi-times
    0xFA: '∨',   # or / greatest common divisor
    0xFB: '⍴',   # rho / shape (variant position)
    0xFC: '∪',   # union / unique
    0xFD: '⌈',   # ceiling / maximum
    0xFE: '∣',   # stile / residue / absolute value
    0xFF: ' ',   # space (position 255)
}
# fmt: on


def decode(data: bytes | bytearray) -> str:
    """Decode APL+Win encoded bytes to a Unicode string.

    Bytes in the standard ASCII range (0x20–0x7E) pass through unchanged.
    Bytes with an entry in :data:`APL_MAP` are translated to the
    corresponding Unicode character.  Tab (0x09) becomes ``'\\t'``.
    LF (0x0A) is silently dropped (CR is the canonical line separator).
    Any remaining unmapped byte ``b`` is rendered as ``«XX»`` where XX
    is the lowercase hex value, making gaps in the mapping visible
    without losing information.

    Parameters
    ----------
    data : bytes or bytearray
        Raw bytes from an APL+Win component file.

    Returns
    -------
    str
        Unicode string with APL symbols, ASCII text, and any unmapped
        byte markers.

    Examples
    --------
    >>> from aplwin_sf import decode
    >>> decode(b'\\x95IO\\x061')
    '⎕IO←1'
    """
    parts: list[str] = []
    for b in data:
        if b in APL_MAP:
            parts.append(APL_MAP[b])
        elif 0x20 <= b <= 0x7E:
            parts.append(chr(b))
        elif b == 0x09:
            parts.append('\t')
        elif b == 0x0A:
            pass  # skip LF; CR (0x0D → \n) is the line separator
        else:
            parts.append(f'«{b:02x}»')
    return ''.join(parts)
