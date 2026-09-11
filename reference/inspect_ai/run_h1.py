from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent
V012 = ROOT / "ICTS_v0_C18_SYNTHETIC_FIRST_v0.1.2.zip"
EXPECTED_V012_SHA256 = "a3f225bd493f297d340688345a686f16cd16df14cf39676621e1d6232b2d070b"
EXPECTED_INSPECT_VERSION = "0.3.263"

def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load_cases(vroot: Path):
    definitions = json.loads((vroot / "synthetic/cases.json").read_text())["cases"]
    rows = []
    for c in definitions:
        rows.append({
            "case_id": c["case_id"],
            "fixture": c["fixture"],
            "topology_name": c["topology"],
            "expected": c["expected"],
            "native": json.loads((vroot / "synthetic/fixtures" / c["fixture"]).read_text()),
            "topology": json.loads((vroot / "synthetic/topologies" / c["topology"]).read_text()),
        })
    return rows

def run_bare(vroot: Path):
    proc = subprocess.run(
        [sys.executable, "reference/bare_python/run_suite.py"],
        cwd=vroot, text=True, capture_output=True
    )
    if proc.returncode != 0:
        raise RuntimeError(f"bare harness failed: {proc.returncode}\n{proc.stdout}\n{proc.stderr}")
    data = json.loads((vroot / "evidence/run_result.json").read_text())
    return {r["case_id"]: r["observed"] for r in data["cases"]}, proc

def run_inspect(rows, log_dir: Path):
    from inspect_ai import eval
    from inspect_harness import make_task

    logs = eval(
        make_task(rows),
        model=None,
        log_dir=str(log_dir),
        display="plain",
    )
    if not logs:
        raise RuntimeError("Inspect returned no EvalLog")
    log = logs[0]
    results = {}
    for sample in log.samples or []:
        if not sample.scores:
            raise RuntimeError(f"Inspect sample {sample.id} has no scores")
        score = next(iter(sample.scores.values()))
        results[str(sample.id)] = score.text
    return results, log

def main():
    if sha256(V012) != EXPECTED_V012_SHA256:
        raise SystemExit("v0.1.2 ZIP hash mismatch")

    try:
        actual_inspect = importlib.metadata.version("inspect-ai")
    except importlib.metadata.PackageNotFoundError:
        raise SystemExit(
            "inspect-ai is not installed. Run: "
            f"{sys.executable} -m pip install inspect-ai=={EXPECTED_INSPECT_VERSION}"
        )
    if actual_inspect != EXPECTED_INSPECT_VERSION:
        raise SystemExit(f"Inspect version mismatch: expected {EXPECTED_INSPECT_VERSION}, got {actual_inspect}")

    with tempfile.TemporaryDirectory(prefix="icts_h1_") as td:
        td = Path(td)
        with zipfile.ZipFile(V012) as z:
            z.extractall(td)
        roots = [p for p in td.iterdir() if p.is_dir()]
        if len(roots) != 1:
            raise SystemExit("unexpected v0.1.2 archive shape")
        vroot = roots[0]

        rows = load_cases(vroot)
        bare_results, bare_proc = run_bare(vroot)

        log_dir = ROOT / "inspect_logs"
        if log_dir.exists():
            shutil.rmtree(log_dir)
        log_dir.mkdir()

        inspect_results, log = run_inspect(rows, log_dir)

        all_ids = sorted(set(bare_results) | set(inspect_results))
        comparisons = []
        mismatch = False
        for cid in all_ids:
            b = bare_results.get(cid)
            i = inspect_results.get(cid)
            expected = next((r["expected"] for r in rows if r["case_id"] == cid), None)
            ok = (b == i == expected)
            mismatch |= not ok
            comparisons.append({
                "case_id": cid,
                "expected": expected,
                "bare_python": b,
                "inspect_ai": i,
                "equivalent": ok,
            })

        result = {
            "gate": "H1",
            "vector": "CORE-PROP-EXT-EVIDENCE-001 / ICTS-VEC-EXT-EVIDENCE-001",
            "v012_zip_sha256": sha256(V012),
            "inspect_ai_version": actual_inspect,
            "bare_python_exit": bare_proc.returncode,
            "comparisons": comparisons,
            "terminal": "H1_PASS" if not mismatch else "H1_FAIL",
            "claim": (
                "Same frozen vector produced identical normative terminal results in "
                "bare-Python and independently implemented Inspect AI harness."
                if not mismatch else
                "Harness equivalence not established."
            ),
        }
        out = ROOT / "H1_RESULT.json"
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if not mismatch else 1)

if __name__ == "__main__":
    main()
