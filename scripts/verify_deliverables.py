"""Check that measured data and both submission packages agree."""

from collections import defaultdict
import csv
import math
from pathlib import Path

import pymupdf


ROOT = Path(__file__).resolve().parent.parent


def check_results(raw_name: str, summary_name: str) -> None:
    with (ROOT / raw_name).open(newline="", encoding="utf-8") as file:
        raw = list(csv.DictReader(file))
    with (ROOT / summary_name).open(newline="", encoding="utf-8") as file:
        summary = {row["config_id"]: row for row in csv.DictReader(file)}
    groups = defaultdict(list)
    for row in raw:
        groups[row["config_id"]].append(row)
    assert len(raw) == 33 and len(groups) == 11 and len(summary) == 11
    assert all(len(rows) == 3 for rows in groups.values())
    assert {(row["n"], row["steps"], row["seed"]) for row in raw} == {
        ("5000", "10", "42")
    }
    seq_checksum = float(groups["sequential"][0]["checksum"])
    assert all(abs(float(row["checksum"]) - seq_checksum) < 1e-9 for row in raw)
    for key, samples in groups.items():
        mean = sum(float(row["elapsed_s"]) for row in samples) / 3
        assert math.isclose(mean, float(summary[key]["elapsed_mean_s"]), abs_tol=1e-9)
        assert summary[key]["repeats"] == "3"


check_results("results_raw.csv", "results.csv")
check_results("results_cpp_raw.csv", "results_cpp.csv")
assert 3 <= len(pymupdf.open(ROOT / "report.pdf")) <= 5
repository = "https://github.com/Jonialen/labPCAM"
for document in [
    ROOT / "report.pdf",
    ROOT / "diseno_pcam_previo.pdf",
    ROOT / "entrega_canvas" / "explicacion_pcam.pdf",
    ROOT / "entrega_canvas" / "evidencia.pdf",
]:
    with pymupdf.open(document) as pdf:
        assert any(link.get("uri") == repository for page in pdf for link in page.get_links())

canvas = ROOT / "entrega_canvas"
assert {p.name for p in canvas.iterdir()} == {
    "nbody_secuencial.c", "nbody_paralelo.c",
    "explicacion_pcam.pdf", "evidencia.pdf", "diseno_pcam_previo.pdf",
}
assert "#pragma omp" not in (canvas / "nbody_secuencial.c").read_text(encoding="utf-8")
assert len(pymupdf.open(canvas / "evidencia.pdf")) == 2
assert len(pymupdf.open(ROOT / "diseno_pcam_previo.pdf")) == 2
assert (canvas / "diseno_pcam_previo.pdf").read_bytes() == (ROOT / "diseno_pcam_previo.pdf").read_bytes()

cpp = ROOT / "entrega_cpp" / "lab-pcam-nbody"
for name in ["nbody_seq.cpp", "nbody_parallel.cpp", "nbody_optimized.cpp"]:
    assert (cpp / "src" / name).is_file()
for name in ["README.md", "Makefile", "report.pdf", "diseno_pcam_previo.pdf", "results.csv", "results_raw.csv"]:
    assert (cpp / name).is_file()
for source, target in [
    ("compile.png", "compile.png"),
    ("cpp_sequential.png", "sequential.png"),
    ("cpp_parallel.png", "parallel.png"),
    ("cpp_optimized.png", "optimized.png"),
    ("hardware.png", "hardware.png"),
    ("correctness.png", "correctness.png"),
]:
    assert (cpp / "evidence" / target).read_bytes() == (ROOT / "evidence" / source).read_bytes()
assert (cpp / "results.csv").read_bytes() == (ROOT / "results_cpp.csv").read_bytes()
assert (cpp / "report.pdf").read_bytes() == (ROOT / "report.pdf").read_bytes()
assert (cpp / "diseno_pcam_previo.pdf").read_bytes() == (ROOT / "diseno_pcam_previo.pdf").read_bytes()
for name in ["results.csv", "results_raw.csv", "results_cpp.csv", "results_cpp_raw.csv"]:
    assert (cpp / "measurements" / name).read_bytes() == (ROOT / name).read_bytes()
print("Verified 66 measured runs, both reports and both submission packages.")
