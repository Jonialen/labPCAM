#!/bin/sh
set -eu

program=${1:?usage: test_cli.sh <nbody-sequential-binary>}
output_one=$("$program" 16 3)
output_two=$("$program" 16 3)

checksum_one=$(printf '%s\n' "$output_one" | sed -n 's/^Checksum: //p')
checksum_two=$(printf '%s\n' "$output_two" | sed -n 's/^Checksum: //p')
[ -n "$checksum_one" ]
[ "$checksum_one" = "$checksum_two" ]
printf '%s\n' "$output_one" | grep -q '^Mode: sequential$'
printf '%s\n' "$output_one" | grep -q '^N: 16 | Steps: 3 | Seed: 42$'
printf '%s\n' "$output_one" | grep -q '^Elapsed: [0-9][0-9.]* s$'
printf '%s\n' "$output_one" | grep -q '^Processors reported by OpenMP: [1-9][0-9]*$'
printf '%s\n' "$output_one" | grep -q '^Maximum threads reported by OpenMP: [1-9][0-9]*$'

if "$program" 0 1 >/dev/null 2>&1; then
    echo "zero body count should be rejected" >&2
    exit 1
fi
if "$program" 10 nope >/dev/null 2>&1; then
    echo "non-numeric step count should be rejected" >&2
    exit 1
fi
echo "CLI tests passed (checksum: $checksum_one)."
