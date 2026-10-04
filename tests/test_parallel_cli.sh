#!/bin/sh
set -eu

program=${1:?usage: test_parallel_cli.sh <nbody-parallel-binary>}
output=$($program 16 3 2 guided 2)
printf '%s\n' "$output" | grep -q '^Mode: parallel-direct$'
printf '%s\n' "$output" | grep -q '^Threads requested: 2 | Threads used: [1-2]$'
printf '%s\n' "$output" | grep -q '^Schedule: guided | Chunk: 2$'
printf '%s\n' "$output" | grep -q '^Elapsed: [0-9][0-9.]* s$'
printf '%s\n' "$output" | grep -q '^Checksum: [-0-9.]*$'
printf '%s\n' "$output" | grep -q '^Processors reported by OpenMP: [1-9][0-9]*$'
printf '%s\n' "$output" | grep -q '^Maximum threads reported by OpenMP: [1-9][0-9]*$'

for args in '0 1 2 static' '10 nope 2 static' '10 2 0 static' '10 2 2 cyclic' '10 2 2 dynamic -1'; do
    if $program $args >/dev/null 2>&1; then
        echo "invalid parallel CLI arguments should be rejected: $args" >&2
        exit 1
    fi
done
echo "Parallel CLI tests passed."
