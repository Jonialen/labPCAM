# C/OpenMP N-body simulation

A reproducible 2D gravitational N-body simulation with matching C11 and C++17 implementations. Each language has a sequential baseline and two OpenMP implementations. The code is organized as a small command-line project and can be built and tested with GNU Make.

## Build and test

Requirements: C11 and C++17 compilers, GNU Make, Python 3, and an OpenMP-capable compiler/runtime. The Makefile prefers `gcc-16`/`g++-16`, then `gcc`/`g++`; set `CC` and `CXX` explicitly if needed. The default flags link OpenMP and `libm`.

```sh
make all
make test
```

`make test` runs numerical tests and CLI checks for both languages, verifies that the C++17 sources match the C reference, and builds/tests the two standalone C sources requested for Canvas. Generated binaries are placed in `build/`; remove them with `make clean`.

## Run a simulation

```sh
build/nbody_seq <bodies> <steps>
build/nbody_parallel <bodies> <steps> <threads> <static|dynamic|guided> [chunk]
build/nbody_optimized <bodies> <steps> <threads> <static|dynamic|guided> [chunk]
```

For example:

```sh
build/nbody_seq 500 10
build/nbody_parallel 500 10 4 static
build/nbody_optimized 500 10 4 guided 8
```

The corresponding C++17 executables have the same names prefixed by `cpp_`, for example `build/cpp_nbody_parallel 500 10 4 static`. The C++17 source copies are in `src_cpp/`; update them after a C source edit with `python3 scripts/sync_cpp.py`.

All numeric arguments must be positive integers. The optional chunk controls OpenMP scheduling granularity; when omitted, the runtime's schedule default is used. Each run initializes the same workload from a fixed seed and reports elapsed time and a checksum. Parallel executables also report the requested and actual thread counts and scheduling configuration.

## Implementations

- **Sequential:** calculates each body's acceleration from all other bodies and advances the system with symplectic Euler integration.
- **Direct OpenMP:** parallelizes the per-body calculations. Each iteration reads the current state and writes one body's next state, avoiding shared force updates; the step barrier preserves dependencies between time steps.
- **Pair-symmetric OpenMP:** evaluates each unordered body pair once. Per-thread acceleration planes collect both bodies' contributions, then a reduction combines them without atomics. This lowers pair evaluations but uses additional memory proportional to thread count times body count.

The tests compare deterministic initialization, integration behavior, and full body state across implementations and supported schedules.

## Benchmarking

Run the benchmark script from any directory:

```sh
bash scripts/benchmark.sh
```

It builds the programs, runs a fixed set of sequential, direct-parallel, and pair-symmetric configurations, and writes raw and summarized CSV output to the repository root. Defaults are 5,000 bodies, 10 steps, and three repetitions per configuration. Override the workload with environment variables, for example:

```sh
N=1000 STEPS=5 REPEATS=5 bash scripts/benchmark.sh
```

Set `RAW_CSV` and `SUMMARY_CSV` to choose different output paths. The script verifies workload consistency, repeated-run checksum stability, and at least three runs per configuration before reporting summary statistics. Timings are machine- and load-dependent; compare results on the same host and treat small samples as indicative rather than universal.

To benchmark the C++17 build independently, run `NBODY_IMPL=cpp bash scripts/benchmark.sh`. It writes `results_cpp_raw.csv` and `results_cpp.csv`. Both summaries include speedup, efficiency, and checksum distance from the sequential baseline.

## Laboratory deliverables

- `entrega_canvas/` contains the four files requested in `docs/entregables_del_laboratorio.md` plus `diseno_pcam_previo.pdf`, added for the verbal design-before-code requirement. Regenerate the sources with `python3 scripts/build_canvas_sources.py`.
- `entrega_cpp/lab-pcam-nbody/` is the self-contained C++17 submission described in the longer brief. Regenerate it with `python scripts/package_cpp.py` after generating the report.
- `report.pdf` has four pages of PCAM analysis, measured results, numerical checks, evidence, and conclusions. The underlying 66 runs are in the four CSV files at the root.
- `diseno_pcam_previo.md` and `diseno_pcam_previo.pdf` document the PCAM decisions and annotated pseudocode independently of the measured results. Regenerate the PDF with `python scripts/render_pcam_design.py`.
- `evidence/logs/` contains the terminal records from `bash scripts/capture_evidence.sh`. The PNG files are real Windows Terminal captures of new WSL executions; regenerate them from a visible Windows desktop with `python scripts/capture_real_evidence.py`. The PDF generator embeds those PNG files without redrawing them.

To regenerate every deliverable after changing the simulation, run in order: `python3 scripts/sync_cpp.py`, `make test`, both benchmark commands above, `bash scripts/capture_evidence.sh`, `python scripts/capture_real_evidence.py` from Windows, `python scripts/make_deliverables.py`, `python scripts/render_pcam_design.py`, `python scripts/package_cpp.py`, and `python scripts/verify_deliverables.py`. PDF generation uses ReportLab, Matplotlib and Pillow; verification uses PyMuPDF.

Both requested submission formats are provided.

## Credits

David Domínguez (23712), Jonathan Diaz (23873), and Luis Padilla (23663).
