"""Keep the C++17 translation-unit copies aligned with the C implementation.

The shared implementation is written in the C/C++ common subset. C++17 builds
compile the .cpp copies with g++, so the three requested C++17 source files
remain inspectable and are checked by the same numerical tests.
"""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
NAMES = (
    "nbody",
    "nbody_seq",
    "nbody_parallel",
    "nbody_optimized",
    "nbody_optimized_main",
)
CHECK = sys.argv[1:] == ["--check"]
if sys.argv[1:] and not CHECK:
    raise SystemExit("Usage: sync_cpp.py [--check]")

destination = ROOT / "src_cpp"
destination.mkdir(exist_ok=True)
pairs = [(ROOT / "src" / f"{name}.c", destination / f"{name}.cpp") for name in NAMES]
pairs.append((ROOT / "src" / "nbody.h", destination / "nbody.h"))

for source, target in pairs:
    data = source.read_bytes().replace(b"\r\n", b"\n")
    if CHECK:
        if not target.exists() or target.read_bytes() != data:
            raise SystemExit(f"C++17 copy out of sync: {target}")
    else:
        target.write_bytes(data)

print("C++17 sources match C reference." if CHECK else "Updated C++17 sources.")
