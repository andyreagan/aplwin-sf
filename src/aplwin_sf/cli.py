"""Command-line interface for aplwin-sf."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .parser import read_file


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="aplwin-sf",
        description="Extract APL+Win component files (.sf) to readable UTF-8 text.",
    )
    parser.add_argument(
        "source",
        help="A .sf file or a directory of .sf files.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output directory.  If omitted, prints to stdout.",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args(argv)

    source = Path(args.source)
    if source.is_file():
        files = [source]
    elif source.is_dir():
        files = sorted(p for p in source.iterdir() if p.suffix.lower() == ".sf")
    else:
        parser.error(f"Not a file or directory: {source}")

    if not files:
        parser.error(f"No .sf files found in {source}")

    out_dir: Path | None = Path(args.output) if args.output else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    total_fns = 0
    total_files = 0

    for filepath in files:
        try:
            cf = read_file(filepath)
        except Exception as exc:
            print(f"  {filepath.name:30s} !! ERROR: {exc}", file=sys.stderr)
            continue

        if not cf.functions:
            continue

        total_fns += len(cf.functions)
        total_files += 1

        if out_dir:
            out_path = out_dir / f"{filepath.stem}.apl"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(f"⍝ === Extracted from {filepath.name} ===\n")
                f.write(f"⍝ === {len(cf.functions)} function(s) ===\n\n")
                for fn in cf.functions:
                    f.write(f"{fn.text}\n\n")
            print(
                f"  {filepath.name:30s} → {len(cf.functions):4d} function(s)",
                file=sys.stderr,
            )
        else:
            for fn in cf.functions:
                print(fn.text)
                print()

    if out_dir:
        print(
            f"\nExtracted {total_fns} functions from {total_files} "
            f"files into {out_dir}/",
            file=sys.stderr,
        )
