"""Tests for aplwin_sf.parser using synthetic .sf fixtures."""

import pytest
from pathlib import Path

from aplwin_sf.parser import read_file, read_functions, Function, ComponentFile


FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture(autouse=True)
def _ensure_fixtures():
    """Regenerate fixtures if they don't exist."""
    if not (FIXTURES / "simple.sf").exists():
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from make_fixtures import build_all

        build_all(FIXTURES)


# ── read_functions ──────────────────────────────────────────────────


class TestSimple:
    def test_extracts_one_function(self):
        fns = read_functions(FIXTURES / "simple.sf")
        assert len(fns) == 1

    def test_function_name(self):
        fn = read_functions(FIXTURES / "simple.sf")[0]
        assert fn.name == "ADD"

    def test_function_text_starts_with_del(self):
        fn = read_functions(FIXTURES / "simple.sf")[0]
        assert fn.text.startswith("∇ R←ADD A;B")

    def test_function_text_ends_with_del(self):
        fn = read_functions(FIXTURES / "simple.sf")[0]
        assert fn.text.strip().endswith("∇")

    def test_function_has_body(self):
        fn = read_functions(FIXTURES / "simple.sf")[0]
        assert "[1]   B←1" in fn.text
        assert "[2]   R←A+B" in fn.text

    def test_raw_bytes_not_empty(self):
        fn = read_functions(FIXTURES / "simple.sf")[0]
        assert len(fn.raw) > 0
        assert fn.raw[0:4] == b"\x20\x20\x20\x20"  # leading spaces

    def test_offset_is_reasonable(self):
        fn = read_functions(FIXTURES / "simple.sf")[0]
        assert fn.offset >= 1056  # at or after component start


class TestMulti:
    def test_extracts_three_functions(self):
        fns = read_functions(FIXTURES / "multi.sf")
        assert len(fns) == 3

    def test_function_names(self):
        names = [fn.name for fn in read_functions(FIXTURES / "multi.sf")]
        assert names == ["TAKE", "IOTA", "PLUS"]

    def test_take_has_quad_io(self):
        fn = read_functions(FIXTURES / "multi.sf")[0]
        assert "⎕IO←1" in fn.text

    def test_take_has_up_arrow(self):
        fn = read_functions(FIXTURES / "multi.sf")[0]
        assert "N↑V" in fn.text

    def test_iota_has_iota_symbol(self):
        fn = read_functions(FIXTURES / "multi.sf")[1]
        assert "⍳N" in fn.text

    def test_plus_has_comment(self):
        fn = read_functions(FIXTURES / "multi.sf")[2]
        assert "⍝ Add two values" in fn.text


class TestSymbols:
    def test_extracts_demo_function(self):
        fns = read_functions(FIXTURES / "symbols.sf")
        assert len(fns) == 1
        assert fns[0].name == "DEMO"

    def test_shape_iota(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "3 4⍴⍳12" in text

    def test_floor_ceiling_divide(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "⌊" in text
        assert "⌈" in text
        assert "÷" in text

    def test_take_drop(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "↑" in text
        assert "↓" in text

    def test_enclose(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "⊂" in text

    def test_transpose_comma_bar(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "⍉" in text
        assert "⍪" in text

    def test_zilde(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "⍬" in text

    def test_match(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "≡" in text

    def test_membership(self):
        text = read_functions(FIXTURES / "symbols.sf")[0].text
        assert "∊" in text


class TestMixed:
    """File with data blobs interleaved with function text."""

    def test_skips_data_finds_functions(self):
        fns = read_functions(FIXTURES / "mixed.sf")
        assert len(fns) == 2

    def test_function_names(self):
        names = [fn.name for fn in read_functions(FIXTURES / "mixed.sf")]
        assert names == ["DOUBLE", "HALF"]

    def test_double_body(self):
        fn = read_functions(FIXTURES / "mixed.sf")[0]
        assert "2×N" in fn.text

    def test_half_body(self):
        fn = read_functions(FIXTURES / "mixed.sf")[1]
        assert "N÷2" in fn.text


class TestEmpty:
    def test_no_functions(self):
        fns = read_functions(FIXTURES / "empty.sf")
        assert fns == []


class TestHighMinus:
    def test_macron(self):
        fn = read_functions(FIXTURES / "high_minus.sf")[0]
        assert "¯1" in fn.text


# ── read_file ───────────────────────────────────────────────────────


class TestReadFile:
    def test_returns_component_file(self):
        cf = read_file(FIXTURES / "simple.sf")
        assert isinstance(cf, ComponentFile)

    def test_path_set(self):
        cf = read_file(FIXTURES / "simple.sf")
        assert "simple.sf" in cf.path

    def test_size_positive(self):
        cf = read_file(FIXTURES / "simple.sf")
        assert cf.size > 0

    def test_accepts_raw_bytes(self):
        data = (FIXTURES / "simple.sf").read_bytes()
        cf = read_file(data)
        assert cf.path == "<bytes>"
        assert len(cf.functions) == 1


# ── Edge cases ──────────────────────────────────────────────────────


class TestEdgeCases:
    def test_tiny_file_no_crash(self):
        fns = read_functions(b"")
        assert fns == []

    def test_random_bytes_no_crash(self):
        import os
        fns = read_functions(os.urandom(256))
        assert isinstance(fns, list)

    def test_marker_at_start_of_file(self):
        """Marker too close to file start (no room for header)."""
        data = b"\x20\x20\x20\x20\xEC\x20" + b"A" * 100
        fns = read_functions(data)
        assert fns == []  # header_off would be negative

    def test_truncated_header(self):
        """Marker present but not enough bytes for header validation."""
        data = b"\x00" * 15 + b"\x20\x20\x20\x20\xEC\x20"
        fns = read_functions(data)
        assert fns == []
