#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
N="${N:-5000}"
STEPS="${STEPS:-10}"
REPEATS="${REPEATS:-3}"
RAW_CSV="${RAW_CSV:-$ROOT_DIR/results_raw.csv}"
SUMMARY_CSV="${SUMMARY_CSV:-$ROOT_DIR/results.csv}"

if ! [[ "$N" =~ ^[1-9][0-9]*$ && "$STEPS" =~ ^[1-9][0-9]*$ && "$REPEATS" =~ ^[1-9][0-9]*$ ]]; then
    echo "N, STEPS and REPEATS must be positive integers." >&2
    exit 2
fi

cd "$ROOT_DIR"
make all
mkdir -p "$(dirname "$RAW_CSV")" "$(dirname "$SUMMARY_CSV")"
printf 'config_id,mode,n,steps,seed,threads_requested,threads_used,schedule,chunk,run,elapsed_s,checksum,omp_num_procs,omp_max_threads\n' > "$RAW_CSV"

run_case() {
    local config_id="$1" mode="$2" requested="$3" schedule="$4" chunk="$5"
    local run output elapsed checksum used procs max_threads
    for run in $(seq 1 "$REPEATS"); do
        if [[ "$mode" == "sequential" ]]; then
            output="$("$ROOT_DIR/build/nbody_seq" "$N" "$STEPS")"
            requested=1
        elif [[ "$mode" == "parallel-direct" ]]; then
            if [[ "$chunk" == "default" ]]; then
                output="$("$ROOT_DIR/build/nbody_parallel" "$N" "$STEPS" "$requested" "$schedule")"
            else
                output="$("$ROOT_DIR/build/nbody_parallel" "$N" "$STEPS" "$requested" "$schedule" "$chunk")"
            fi
        else
            if [[ "$chunk" == "default" ]]; then
                output="$("$ROOT_DIR/build/nbody_optimized" "$N" "$STEPS" "$requested" "$schedule")"
            else
                output="$("$ROOT_DIR/build/nbody_optimized" "$N" "$STEPS" "$requested" "$schedule" "$chunk")"
            fi
        fi
        elapsed="$(sed -n 's/^Elapsed: \([0-9.]*\) s$/\1/p' <<< "$output")"
        checksum="$(sed -n 's/^Checksum: //p' <<< "$output")"
        used="$(sed -n 's/^Threads requested: [0-9]* | Threads used: \([0-9]*\)$/\1/p' <<< "$output")"
        procs="$(sed -n 's/^Processors reported by OpenMP: //p' <<< "$output")"
        max_threads="$(sed -n 's/^Maximum threads reported by OpenMP: //p' <<< "$output")"
        if [[ -z "$elapsed" || -z "$checksum" || -z "$procs" || -z "$max_threads" ]]; then
            printf 'Failed to parse output for %s run %s\n%s\n' "$config_id" "$run" "$output" >&2
            exit 1
        fi
        if [[ "$mode" == "sequential" ]]; then
            used=1
            schedule="none"
            chunk="none"
        fi
        printf '%s,%s,%s,%s,42,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
            "$config_id" "$mode" "$N" "$STEPS" "$requested" "$used" \
            "$schedule" "$chunk" "$run" "$elapsed" "$checksum" "$procs" "$max_threads" \
            >> "$RAW_CSV"
        printf '%-30s run %s/%s: %ss checksum=%s threads=%s\n' \
            "$config_id" "$run" "$REPEATS" "$elapsed" "$checksum" "$used"
    done
}

run_case sequential sequential 1 none none
run_case direct_2_static_default parallel-direct 2 static default
run_case direct_4_static_default parallel-direct 4 static default
run_case direct_8_static_default parallel-direct 8 static default
run_case direct_8_static_chunk8 parallel-direct 8 static 8
run_case direct_8_static_chunk32 parallel-direct 8 static 32
run_case direct_8_static_chunk64 parallel-direct 8 static 64
run_case direct_8_dynamic_chunk8 parallel-direct 8 dynamic 8
run_case direct_8_dynamic_chunk64 parallel-direct 8 dynamic 64
run_case direct_8_guided_default parallel-direct 8 guided default
run_case optimized_8_static_default pair-symmetric-optimized 8 static default

python3 - "$RAW_CSV" "$SUMMARY_CSV" <<'PY'
import csv
import statistics
import sys

raw_path, summary_path = sys.argv[1:3]
with open(raw_path, newline="", encoding="utf-8") as stream:
    rows = list(csv.DictReader(stream))
groups = {}
for row in rows:
    groups.setdefault(row["config_id"], []).append(row)

seq_mean = statistics.mean(float(row["elapsed_s"]) for row in groups["sequential"])
direct_mean = statistics.mean(
    float(row["elapsed_s"]) for row in groups["direct_8_static_default"]
)
optimized_mean = statistics.mean(
    float(row["elapsed_s"]) for row in groups["optimized_8_static_default"]
)
fieldnames = [
    "config_id", "mode", "n", "steps", "seed", "threads_requested",
    "threads_used_mean", "schedule", "chunk", "repeats", "elapsed_mean_s",
    "elapsed_sd_s", "elapsed_min_s", "elapsed_max_s", "speedup_vs_seq",
    "efficiency", "checksum_first", "max_abs_checksum_delta_vs_first",
    "relative_to_direct_8_static_default",
]
with open(summary_path, "w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    for config_id, samples in groups.items():
        times = [float(row["elapsed_s"]) for row in samples]
        checksums = [float(row["checksum"]) for row in samples]
        threads = statistics.mean(int(row["threads_used"]) for row in samples)
        mean = statistics.mean(times)
        mode = samples[0]["mode"]
        writer.writerow({
            "config_id": config_id,
            "mode": mode,
            "n": samples[0]["n"],
            "steps": samples[0]["steps"],
            "seed": samples[0]["seed"],
            "threads_requested": samples[0]["threads_requested"],
            "threads_used_mean": f"{threads:.6f}",
            "schedule": samples[0]["schedule"],
            "chunk": samples[0]["chunk"],
            "repeats": len(samples),
            "elapsed_mean_s": f"{mean:.9f}",
            "elapsed_sd_s": f"{statistics.stdev(times) if len(times) > 1 else 0.0:.9f}",
            "elapsed_min_s": f"{min(times):.9f}",
            "elapsed_max_s": f"{max(times):.9f}",
            "speedup_vs_seq": f"{seq_mean / mean:.6f}",
            "efficiency": f"{seq_mean / mean / threads:.6f}",
            "checksum_first": f"{checksums[0]:.12f}",
            "max_abs_checksum_delta_vs_first": f"{max(abs(value - checksums[0]) for value in checksums):.12g}",
            "relative_to_direct_8_static_default": (
                f"{direct_mean / mean:.6f}" if mode == "pair-symmetric-optimized"
                else "1.000000" if config_id == "direct_8_static_default"
                else ""
            ),
        })

if len(rows) != sum(len(group) for group in groups.values()):
    raise SystemExit("Raw-result grouping check failed.")
if any(len(group) < 3 for group in groups.values()):
    raise SystemExit("Every configuration must have at least three measured runs.")
if len({(row["n"], row["steps"], row["seed"]) for row in rows}) != 1:
    raise SystemExit("Workload consistency check failed.")
if any(float(row["max_abs_checksum_delta_vs_first"]) != 0.0 for row in csv.DictReader(open(summary_path, newline="", encoding="utf-8"))):
    raise SystemExit("Non-deterministic checksum across repeated runs.")
print(f"Wrote {len(rows)} raw runs across {len(groups)} configurations to {raw_path}")
print(f"Summary written to {summary_path}; sequential mean={seq_mean:.9f}s")
PY
