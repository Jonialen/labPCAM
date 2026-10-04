# C/OpenMP N-body simulation

A reproducible 2D gravitational N-body simulation in C, with a sequential baseline and two OpenMP implementations. The code is organized as a small command-line project and can be built and tested with GNU Make.

## Build and test

Requirements: a C11 compiler, GNU Make, and an OpenMP-capable compiler/runtime. The Makefile prefers `gcc-16`, then `gcc`, then `cc`; set `CC` explicitly if needed. The default flags link OpenMP and `libm`.

```sh
make all
make test
```

`make test` runs the numerical tests and CLI checks for all three executables. Generated binaries are placed in `build/`; remove them with `make clean`.

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

## Credits

Jonathan Díaz, David Dominguez, and Luis Padilla.
