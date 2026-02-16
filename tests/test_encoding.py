"""Tests for aplwin_sf.encoding."""

from aplwin_sf.encoding import APL_MAP, decode


class TestAPLMap:
    def test_assignment(self):
        assert APL_MAP[0x06] == "←"

    def test_quad(self):
        assert APL_MAP[0x95] == "⎕"

    def test_comment(self):
        assert APL_MAP[0xA6] == "⍝"

    def test_iota(self):
        assert APL_MAP[0xE2] == "⍳"

    def test_rho(self):
        assert APL_MAP[0x86] == "⍴"
        assert APL_MAP[0xFB] == "⍴"  # variant position

    def test_times(self):
        assert APL_MAP[0x19] == "×"
        assert APL_MAP[0x8F] == "×"
        assert APL_MAP[0x92] == "×"

    def test_high_minus(self):
        assert APL_MAP[0xEF] == "¯"

    def test_floor_ceiling(self):
        assert APL_MAP[0xE8] == "⌊"
        assert APL_MAP[0xFD] == "⌈"

    def test_cr_maps_to_newline(self):
        assert APL_MAP[0x0D] == "\n"

    def test_covers_all_apl_symbols(self):
        """Every common APL symbol should be reachable."""
        symbols = set(APL_MAP.values())
        for ch in "←→↑↓⍴⍳⎕⍝∇⍺⍵∊⍕⍎⌊⌈÷×∨∘○≡≥≤⍟⊂⊃⍪⍨⌹⌷⊥⊤⍉⊖⌿⍀":
            assert ch in symbols, f"Missing APL symbol: {ch}"


class TestDecode:
    def test_ascii_passthrough(self):
        assert decode(b"Hello") == "Hello"

    def test_quad_io(self):
        assert decode(b"\x95IO\x061") == "⎕IO←1"

    def test_comment(self):
        assert decode(b"\xa6 This is a comment") == "⍝ This is a comment"

    def test_cr_becomes_newline(self):
        assert decode(b"line1\x0dline2") == "line1\nline2"

    def test_lf_dropped(self):
        assert decode(b"A\x0aB") == "AB"

    def test_tab_preserved(self):
        assert decode(b"A\x09B") == "A\tB"

    def test_iota_n(self):
        assert decode(b"\xe2N") == "⍳N"

    def test_shape(self):
        # "3 4⍴⍳12"
        assert decode(b"3 4\xfb\xe212") == "3 4⍴⍳12"

    def test_floor_ceiling_divide(self):
        assert decode(b"\xe80.5+\xfd\xf62") == "⌊0.5+⌈÷2"

    def test_high_minus(self):
        assert decode(b"\xef1") == "¯1"

    def test_unmapped_bytes_marked(self):
        assert decode(b"\x00") == "«00»"
        assert decode(b"\x02") == "«02»"

    def test_empty(self):
        assert decode(b"") == ""

    def test_del(self):
        assert decode(b"\xec") == "∇"

    def test_branch(self):
        assert decode(b"\x1a0") == "→0"

    def test_full_line(self):
        # "[1]   ⎕IO←1"
        raw = b"[1]   \x95IO\x061"
        assert decode(raw) == "[1]   ⎕IO←1"
