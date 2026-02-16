# aplwin-sf

Read APL+Win component files (`.sf`) from Python.

APL+Win stores source code and data in a proprietary binary format called
"component files" (file extension `.sf`). This library parses them and decodes
APL+Win's character encoding to Unicode, producing readable UTF-8 text.

## Installation

```
pip install aplwin-sf
```

## Quick start

### Python API

```python
from aplwin_sf import read_functions

for fn in read_functions("myfuncs.sf"):
    print(fn.name, len(fn.text), "chars")
```

```python
from aplwin_sf import decode

raw = b"\x95IO\x061"
print(decode(raw))  # ⎕IO←1
```

### Command line

```bash
# Print all functions to stdout
aplwin-sf myfuncs.sf

# Extract a directory of .sf files to .apl text files
aplwin-sf /path/to/sf/files/ -o apl_source/
```

## What it does

1. **Parses the binary `.sf` format** — scans for function-text sub-objects
   by looking for the `∇` (del) marker that begins every APL function definition.

2. **Decodes APL+Win's character encoding** — a single-byte encoding based on
   Code Page 437 with APL symbol overlays. Maps bytes like `0x95` → `⎕`,
   `0x06` → `←`, `0xE2` → `⍳`, etc.

3. **Extracts function metadata** — parses function names from headers,
   handling niladic, monadic, and dyadic forms.

## API

### `read_functions(source) → list[Function]`

Extract all APL functions from a `.sf` file.

- `source` — a file path (`str` or `Path`) or raw `bytes`
- Returns a list of `Function(name, text, offset, raw)` objects

### `read_file(source) → ComponentFile`

Read a `.sf` file and return a `ComponentFile(path, functions, size)`.

### `decode(data: bytes) → str`

Decode APL+Win encoded bytes to a Unicode string.

### `APL_MAP: dict[int, str]`

The complete byte → Unicode character mapping table.

## Background

APL+Win is a commercial APL implementation for Windows, originally by
Manugistics (now APL2000/Cognizant). It stores APL objects — functions,
variables, arrays — in "component files" with the `.sf` extension.

These files use a proprietary binary format with no public documentation.
This library was developed by reverse-engineering the format from real `.sf`
files, with the character encoding cross-referenced against the `∆AV` table
from [Dyalog's aplwincfs project](https://github.com/Dyalog/aplwincfs).

### Character encoding notes

APL+Win's file encoding is **not** the same as the `⎕AV` (atomic vector)
mapping. The `⎕AV` maps logical character positions; the file encoding maps
raw byte values from the APL+Win font/codepage. For example:

| Byte | File encoding | Dyalog ∆AV |
|------|---------------|------------|
| 0x86 | `⍴` (rho)     | `≠`        |
| 0x8D | `↓` (drop)    | `⌈`        |
| 0x8F | `×` (times)   | `⌊`        |
| 0xE8 | `⌊` (floor)   | `⌽`        |
| 0xFD | `⌈` (ceiling) | `¯`        |

The file encoding in this library was validated against actual APL source
code in context (e.g., `10×` must be "ten times", not "ten floor").

## License

MIT
