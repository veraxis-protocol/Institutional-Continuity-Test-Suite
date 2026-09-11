from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, platform, sys

from icts_core import adjudicate, normalize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FIX = ROOT / "synthetic" / "fixtures"
TOP = ROOT / "synthetic" / "topologies"
NORM = ROOT / "synthetic" / "expected_normalized"
EVID = ROOT / "evidence"
EVID.mkdir(exist_ok=True)

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def verify_manifest():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    mismatches = []
    for rel, meta in manifest["files"].items():
        p = ROOT / rel
        if not p.exists():
            mismatches.append({"path": rel, "error": "missing"})
            continue
        got = sha256_file(p)
        if got != meta["sha256"]:
            mismatches.append({"path": rel, "expected": meta["sha256"], "observed": got})
    return manifest, mismatches

def mapper_conformance(fixture_name, native):
    if fixture_name == "invalid_missing_event_id_001.json":
        try:
            normalize(native)
        except Exception:
            return True, "expected normalization rejection"
        return False, "malformed native event unexpectedly normalized"

    p = NORM / f"{fixture_name}.normalized.json"
    if not p.exists():
        return False, "frozen expected-normalized oracle missing"
    observed = normalize(native)
    expected = json.loads(p.read_text())
    return observed == expected, "exact match" if observed == expected else "normalized output differs from frozen oracle"

def main():
    manifest, manifest_errors = verify_manifest()
    if manifest_errors:
        bundle = {
            "suite": "ICTS v0 C18-derived synthetic-first v0.1.2",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "result": "INVALID_TEST_EXECUTION",
            "manifest_errors": manifest_errors,
        }
        print(json.dumps(bundle, indent=2, sort_keys=True))
        return 2

    case_def = json.loads((ROOT / "synthetic" / "cases.json").read_text())["cases"]
    results = []
    failures = []
    mapper_failures = []

    for c in case_def:
        native = json.loads((FIX / c["fixture"]).read_text())
        topology = json.loads((TOP / c["topology"]).read_text())
        mapper_ok, mapper_note = mapper_conformance(c["fixture"], native)
        if not mapper_ok:
            mapper_failures.append({"case_id": c["case_id"], "fixture": c["fixture"], "note": mapper_note})
        result = adjudicate(native, topology)
        row = {
            "case_id": c["case_id"],
            "fixture": c["fixture"],
            "topology": c["topology"],
            "expected": c["expected"],
            "observed": result["result"],
            "evidence_path": result.get("evidence_path"),
            "details": result.get("details", []),
            "fixture_sha256": sha256_file(FIX / c["fixture"]),
            "topology_sha256": sha256_file(TOP / c["topology"]),
        }
        results.append(row)
        if result["result"] != c["expected"]:
            failures.append(row)

    topology_eligible_valid_cases = [
        r for r in results
        if r["expected"] not in {"NOT_APPLICABLE_TOPOLOGY", "INVALID_TEST_EXECUTION"}
    ]
    adjudicable_cases = [r for r in topology_eligible_valid_cases if r["observed"] in {"PASS", "FAIL"}]

    command = "python3 reference/bare_python/run_suite.py"
    bundle = {
        "suite": "ICTS v0 C18-derived synthetic-first v0.1.2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "command": command,
        "manifest_sha256": sha256_file(ROOT / "MANIFEST.json"),
        "bound_artifacts": {
            "property_sha256": sha256_file(ROOT / "spec/core/CORE-PROP-EXT-EVIDENCE-001.md"),
            "npc_sha256": sha256_file(ROOT / "spec/icts/NPC-EXT-EVIDENCE-001.json"),
            "esc_sha256": sha256_file(ROOT / "spec/icts/ESC-EXT-EVIDENCE-001.json"),
            "vector_sha256": sha256_file(ROOT / "spec/icts/ICTS-VEC-EXT-EVIDENCE-001.json"),
            "cases_sha256": sha256_file(ROOT / "synthetic/cases.json"),
        },
        "mapper_conformance": {
            "passed": not mapper_failures,
            "failures": mapper_failures,
            "oracle_policy": "Frozen expected-normalized files are required; missing oracle is a failure, never regenerated."
        },
        "cases": results,
        "synthetic_case_adjudicability": {
            "k": len(adjudicable_cases),
            "n": len(topology_eligible_valid_cases),
            "definition": "PASS/FAIL cases divided by topology-eligible structurally valid synthetic test cases; NOT an EPSR and NOT a deployment metric."
        },
        "field_epsr": "FIELD_EPSR_PENDING",
        "failures": failures,
        "terminal": "PASS" if not failures and not mapper_failures else "FAIL"
    }

    out = EVID / "run_result.json"
    out.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    print(json.dumps(bundle, indent=2, sort_keys=True))
    return 0 if bundle["terminal"] == "PASS" else 1

if __name__ == "__main__":
    raise SystemExit(main())
