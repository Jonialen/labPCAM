"""Assemble the self-contained C++17 submission described in the long brief."""

from pathlib import Path
from shutil import copy2


ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "entrega_cpp" / "lab-pcam-nbody"
(DEST / "src").mkdir(parents=True, exist_ok=True)
(DEST / "evidence" / "logs").mkdir(parents=True, exist_ok=True)
(DEST / "measurements").mkdir(parents=True, exist_ok=True)

for source in (ROOT / "src_cpp").iterdir():
    if source.suffix in {".cpp", ".h"}:
        copy2(source, DEST / "src" / source.name)

for source_name, target_name in [
    ("results_cpp.csv", "results.csv"),
    ("results_cpp_raw.csv", "results_raw.csv"),
    ("report.pdf", "report.pdf"),
    ("diseno_pcam_previo.pdf", "diseno_pcam_previo.pdf"),
]:
    copy2(ROOT / source_name, DEST / target_name)

for name in ["results.csv", "results_raw.csv", "results_cpp.csv", "results_cpp_raw.csv"]:
    copy2(ROOT / name, DEST / "measurements" / name)

for source_name, target_name in [
    ("compile.png", "compile.png"),
    ("cpp_sequential.png", "sequential.png"),
    ("cpp_parallel.png", "parallel.png"),
    ("cpp_optimized.png", "optimized.png"),
    ("hardware.png", "hardware.png"),
    ("correctness.png", "correctness.png"),
]:
    copy2(ROOT / "evidence" / source_name, DEST / "evidence" / target_name)

for source_name, target_name in [
    ("compile.txt", "compile.txt"),
    ("cpp_sequential.txt", "sequential.txt"),
    ("cpp_parallel.txt", "parallel.txt"),
    ("cpp_optimized.txt", "optimized.txt"),
    ("hardware.txt", "hardware.txt"),
    ("correctness.txt", "correctness.txt"),
    ("benchmark_cpp.txt", "benchmark_cpp.txt"),
]:
    copy2(ROOT / "evidence" / "logs" / source_name,
          DEST / "evidence" / "logs" / target_name)

(DEST / "Makefile").write_text("""CXX := $(shell command -v g++-16 2>/dev/null || command -v g++ 2>/dev/null || command -v c++)
CXXFLAGS ?= -std=c++17 -O2 -Wall -Wextra -Wpedantic -fopenmp
LDLIBS ?= -lm

.PHONY: all clean
all: nbody_seq nbody_parallel nbody_optimized

nbody_seq: src/nbody_seq.cpp src/nbody.cpp src/nbody.h
\t$(CXX) $(CXXFLAGS) src/nbody_seq.cpp src/nbody.cpp -o $@ $(LDLIBS)

nbody_parallel: src/nbody_parallel.cpp src/nbody.cpp src/nbody.h
\t$(CXX) $(CXXFLAGS) src/nbody_parallel.cpp src/nbody.cpp -o $@ $(LDLIBS)

nbody_optimized: src/nbody_optimized_main.cpp src/nbody_optimized.cpp src/nbody.cpp src/nbody.h
\t$(CXX) $(CXXFLAGS) src/nbody_optimized_main.cpp src/nbody_optimized.cpp src/nbody.cpp -o $@ $(LDLIBS)

clean:
\trm -f nbody_seq nbody_parallel nbody_optimized
""", encoding="utf-8", newline="\n")

(DEST / "README.md").write_text("""# Entrega C++17 · Laboratorio PCAM + OpenMP

Integrantes: David Domínguez (23712), Jonathan Diaz (23873), Luis Padilla (23663).

Compilar con `make all` usando G++ con OpenMP. Ejecutar:

```sh
./nbody_seq 5000 10
./nbody_parallel 5000 10 8 static
./nbody_optimized 5000 10 8 static
```

`results.csv` resume tres repeticiones por configuración; `results_raw.csv`
conserva las 33 mediciones C++17. `measurements/` conserva los cuatro CSV
originales, incluidos los datos C11 con los que se compara C++17.
`report.pdf` explica PCAM, comparación C/C++17,
corrección y conclusiones. `evidence/` contiene la compilación, las
ejecuciones, el hardware y la comparación numérica.
`diseno_pcam_previo.pdf` presenta el diseño PCAM con pseudocódigo anotado.

Los fuentes `.cpp` compilan con `-std=c++17`. Se mantienen sincronizados con
la referencia C11 del repositorio mediante `scripts/sync_cpp.py` y pasan la
misma suite numérica y de CLI.
""", encoding="utf-8", newline="\n")

print(f"Packaged C++17 submission at {DEST}")
