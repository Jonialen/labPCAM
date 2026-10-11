"""Create the two self-contained C source files requested for Canvas."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "src"
OUTPUT = ROOT / "entrega_canvas"


def read_source(name: str) -> str:
    text = (SOURCE / name).read_text(encoding="utf-8")
    return text.replace('#include "nbody.h"\n', "", 1)


SEQUENTIAL_HEADER = """#ifndef NBODY_H
#define NBODY_H
#include <stddef.h>
#include <stdint.h>
#define NBODY_SEED UINT64_C(42)
#define NBODY_DT 0.001
#define NBODY_GRAVITATIONAL_CONSTANT 1.0
#define NBODY_SOFTENING 0.01
#define NBODY_MIN_MASS 0.5
#define NBODY_MAX_MASS 10.0
typedef struct { double x, y, vx, vy, mass; } Body;
void nbody_initialize(Body *bodies, size_t count, uint64_t seed);
void nbody_step(const Body *current, Body *next, size_t count);
int nbody_simulate(Body *bodies, size_t count, size_t steps);
double nbody_checksum(const Body *bodies, size_t count);
int nbody_parse_positive_size(const char *text, size_t *value);
#endif
"""


def write_program(destination: str, main_source: str, sequential_only: bool) -> None:
    OUTPUT.mkdir(exist_ok=True)
    header = (SEQUENTIAL_HEADER if sequential_only else
              (SOURCE / "nbody.h").read_text(encoding="utf-8"))
    common = read_source("nbody.c")
    if sequential_only:
        start = common.index("static int nbody_openmp_schedule(")
        end = common.index("int nbody_simulate(Body *", start)
        common = common[:start] + common[end:]
        common = common.replace("#include <omp.h>\n", "", 1)
    main = read_source(main_source)
    program = (
        "/* Archivo independiente generado desde src/. No editar esta copia. */\n"
        + header
        + "\n"
        + common
        + "\n"
        + main
    )
    (OUTPUT / destination).write_text(program, encoding="utf-8", newline="\n")


write_program("nbody_secuencial.c", "nbody_seq.c", sequential_only=True)
write_program("nbody_paralelo.c", "nbody_parallel.c", sequential_only=False)
