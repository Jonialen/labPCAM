#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
mkdir -p evidence/logs

{
    printf 'UTC: '
    date -u '+%Y-%m-%dT%H:%M:%SZ'
    printf 'Git revision: '
    git rev-parse --short HEAD
    uname -a
    printf 'Compiler C: '
    gcc --version | head -n 1
    printf 'Compiler C++: '
    g++ --version | head -n 1
    lscpu | grep -E '^(Architecture|CPU\(s\)|Model name|Thread\(s\) per core|Core\(s\) per socket|Socket\(s\)):'
} | tee evidence/logs/hardware.txt

make -B all 2>&1 | tee evidence/logs/compile.txt
make test 2>&1 | tee evidence/logs/tests.txt

{
    printf '$ build/nbody_seq 5000 10\n'
    build/nbody_seq 5000 10
} | tee evidence/logs/sequential.txt
{
    printf '$ build/nbody_parallel 5000 10 8 static\n'
    build/nbody_parallel 5000 10 8 static
} | tee evidence/logs/parallel.txt
{
    printf '$ build/nbody_optimized 5000 10 8 static\n'
    build/nbody_optimized 5000 10 8 static
} | tee evidence/logs/optimized.txt

{
    printf '$ build/cpp_nbody_seq 5000 10\n'
    build/cpp_nbody_seq 5000 10
    printf '$ build/cpp_nbody_parallel 5000 10 8 static\n'
    build/cpp_nbody_parallel 5000 10 8 static
    printf '$ build/cpp_nbody_optimized 5000 10 8 static\n'
    build/cpp_nbody_optimized 5000 10 8 static
} | tee evidence/logs/cpp_runs.txt

{
    printf '$ build/compare_full_state 5000 10\n'
    build/compare_full_state 5000 10
    printf '$ build/cpp_compare_full_state 5000 10\n'
    build/cpp_compare_full_state 5000 10
} | tee evidence/logs/correctness.txt
