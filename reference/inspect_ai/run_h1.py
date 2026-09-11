"""ICTS H1 gate runner -- ICTS_H1_INSPECT_v0.1.1.

H1 asks one narrow question:

    Does the same frozen institutional property/vector produce identical
    normative terminal results when implemented through two independent
    harness implementations?

    Harness A: reference/bare_python/      (frozen ICTS v0.1.2)
    Harness B: reference/inspect_ai/       (independent Inspect AI implementation)

H1 is NOT a claim about field validity, field EPSR, H2, vendor conformance, or
all-suite conformance. It is one vector, two implementations.

Input modes
-----------
Exactly one is required. No directory is ever searched implicitly.

    python reference/inspect_ai/run_h1.py --frozen-tree .
    python reference/inspect_ai/run_h1.py --frozen-zip /path/to/ICTS_v0_C18_SYNTHETIC_FIRST_v0.1.2.zip

--frozen-tree PATH
    PATH is the repository root. The v0.1.2 integrity gate runs FIRST: all 42
    frozen manifest entries are verified byte-for-byte, then the exact frozen
    package is reconstituted in a temporary directory.

--frozen-zip PATH
    PATH is the frozen v0.1.2 archive. Its SHA-256 is verified against the
    frozen digest before extraction.

Both modes converge on the same frozen normative inputs, and neither weakens
frozen-package verification.

Terminal states
---------------
    H1_PASS          every frozen case: bare == inspect == expected   (exit 0)
    H1_FAIL          any case differs                                 (exit 1)
    H1_NOT_EXECUTED  environment/runtime prevented execution          (exit 2)

An execution failure is never converted into a pass.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

H1_VERSION = "0.1.1"
ICTS_VERSION = "0.1.2"
VECTOR = "ICTS-VEC-EXT-EVIDENCE-001"
PROPERTY = "CORE-PROP-EXT-EVIDENCE-001"

EXPECTED_INSPECT_VERSION = "0.3.263"
EXPECTED_V012_ZIP_SHA256 = (
    "a3f225bd493f297d340688345a686f16cd16df14cf39676621e1d6232b2d070b"
)
EXPECTED_MANIFEST_SHA256 = (
    "920d390714cc9593cf0a79c1caf80f2566419e2fa05d6e12cb9c403b20f0040f"
)

# Markers naming the bare-Python reference implementation. The Inspect harness
# must not import or invoke anything behind them.
BARE_PYTHON_MARKERS = ("icts_core", "bare_python")

RESULT_VOCABULARY = {
    "PASS",
    "FAIL",
    "NOT_TESTABLE",
    "NOT_APPLICABLE_TOPOLOGY",
    "INVALID_TEST_EXECUTION",
}


class H1NotExecuted(RuntimeError):
    """Raised when the environment prevents the gate from running at all."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_commit(path: Path):
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            return None
        return proc.stdout.strip() or None
    except Exception:
        return None


# --------------------------------------------------------------------------
# Independence check (mechanical, not assumed)
# --------------------------------------------------------------------------

def check_independence() -> dict:
    """Mechanically confirm the Inspect harness does not use bare-Python code.

    Combines static inspection of inspect_harness.py with runtime inspection of
    the imported module. Populated from actual inspection, never assumed.
    """
    harness_path = HERE / "inspect_harness.py"
    source = harness_path.read_text()
    tree = ast.parse(source)

    # 1. Static: no import of the bare-Python reference implementation.
    imported: list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module)
    imports_bare_python = any(
        marker in name for name in imported for marker in BARE_PYTHON_MARKERS
    )

    # 2. Static: no textual reference at all, which also catches importlib,
    #    exec, or subprocess routes into the bare-Python implementation.
    textual_refs = sorted({m for m in BARE_PYTHON_MARKERS if m in source})

    # 3. Static: the normative evaluation path is defined in this module.
    defined = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    required = {"normalize", "evidence_sufficient", "invariant_holds", "adjudicate"}
    missing = sorted(required - defined)

    # 4. Runtime: importing the harness must not pull in bare-Python modules,
    #    and the normative functions must belong to the harness itself.
    sys.path.insert(0, str(HERE))
    try:
        import inspect_harness
    except Exception as exc:
        raise H1NotExecuted(
            f"Inspect harness failed to import: {type(exc).__name__}: {exc}"
        ) from exc

    leaked = sorted(
        name
        for name in sys.modules
        if any(marker in name for marker in BARE_PYTHON_MARKERS)
    )

    owned = {
        fn: getattr(inspect_harness, fn).__module__ == "inspect_harness"
        for fn in sorted(required)
        if hasattr(inspect_harness, fn)
    }

    record = {
        "h1_version": H1_VERSION,
        "inspect_imports_bare_python": bool(imports_bare_python),
        "shared_normative_inputs_only": True,
        "independent_normalization": owned.get("normalize", False),
        "independent_evidence_sufficiency": owned.get("evidence_sufficient", False),
        "independent_invariant_adjudication": owned.get("invariant_holds", False),
        "method": {
            "static_imports_observed": sorted(set(imported)),
            "bare_python_textual_references": textual_refs,
            "required_normative_functions_defined_locally": sorted(
                required - set(missing)
            ),
            "missing_normative_functions": missing,
            "bare_python_modules_loaded_after_import": leaked,
            "function_module_ownership": owned,
        },
        "note": (
            "Both harnesses consume the same frozen normative inputs (property, "
            "ESC, NPC, topology declarations, fixtures, case set). They implement "
            "the normative evaluation path independently. run_h1.py executes the "
            "bare-Python suite as a separate subprocess to obtain the comparison "
            "baseline; the Inspect harness itself never imports or invokes it."
        ),
    }

    record["independent"] = bool(
        not record["inspect_imports_bare_python"]
        and not textual_refs
        and not leaked
        and not missing
        and record["independent_normalization"]
        and record["independent_evidence_sufficiency"]
        and record["independent_invariant_adjudication"]
    )
    return record


# --------------------------------------------------------------------------
# Frozen input resolution
# --------------------------------------------------------------------------

def frozen_tree_from_repo(repo_root: Path, workdir: Path) -> Path:
    """Verify the repository's frozen inputs, then reconstitute the package."""
    gate = repo_root / "scripts" / "verify_frozen_package.py"
    if not gate.exists():
        raise H1NotExecuted(
            f"--frozen-tree {repo_root} does not look like the ICTS repository "
            "(missing scripts/verify_frozen_package.py)"
        )

    spec = importlib.util.spec_from_file_location("_icts_frozen_gate", gate)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise H1NotExecuted("could not load the frozen-package integrity gate")
    spec.loader.exec_module(module)

    manifest, manifest_sha, problems = module.verify_frozen_files()
    if problems:
        raise H1NotExecuted(
            "frozen v0.1.2 integrity gate failed:\n  " + "\n  ".join(problems)
        )
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise H1NotExecuted(f"frozen manifest digest mismatch: {manifest_sha}")

    print(f"OK: frozen manifest digest {manifest_sha}")
    print(f"OK: {len(manifest['files'])} frozen entries verified byte-for-byte")
    return module.materialize_frozen_package(workdir)


def frozen_tree_from_zip(zip_path: Path, workdir: Path) -> Path:
    """Verify the frozen ZIP digest, then extract it."""
    if not zip_path.is_file():
        raise H1NotExecuted(f"--frozen-zip {zip_path} does not exist")

    observed = sha256_file(zip_path)
    if observed != EXPECTED_V012_ZIP_SHA256:
        raise H1NotExecuted(
            "frozen v0.1.2 ZIP digest mismatch\n"
            f"    expected {EXPECTED_V012_ZIP_SHA256}\n"
            f"    observed {observed}"
        )
    print(f"OK: frozen ZIP digest {observed}")

    extract_to = workdir / "zip"
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_to)

    roots = [p for p in extract_to.iterdir() if p.is_dir()]
    if len(roots) != 1:
        raise H1NotExecuted("unexpected v0.1.2 archive shape")
    vroot = roots[0]

    manifest_sha = sha256_file(vroot / "MANIFEST.json")
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        raise H1NotExecuted(f"frozen manifest digest mismatch: {manifest_sha}")
    print(f"OK: frozen manifest digest {manifest_sha}")
    return vroot


# --------------------------------------------------------------------------
# The two harnesses
# --------------------------------------------------------------------------

def load_case_rows(vroot: Path) -> list:
    """Load the frozen case set. Shared normative inputs, nothing more."""
    definitions = json.loads((vroot / "synthetic/cases.json").read_text())["cases"]
    rows = []
    for c in definitions:
        rows.append(
            {
                "case_id": c["case_id"],
                "fixture": c["fixture"],
                "topology_name": c["topology"],
                "expected": c["expected"],
                "native": json.loads(
                    (vroot / "synthetic/fixtures" / c["fixture"]).read_text()
                ),
                "topology": json.loads(
                    (vroot / "synthetic/topologies" / c["topology"]).read_text()
                ),
            }
        )
    return rows


def run_bare_python(vroot: Path):
    """Harness A: the frozen bare-Python suite, as a separate subprocess."""
    proc = subprocess.run(
        [sys.executable, "reference/bare_python/run_suite.py"],
        cwd=vroot,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise H1NotExecuted(
            f"bare-Python harness exited {proc.returncode}\n"
            f"{proc.stdout[-2000:]}\n{proc.stderr[-2000:]}"
        )
    bundle = json.loads((vroot / "evidence/run_result.json").read_text())
    return {r["case_id"]: r["observed"] for r in bundle["cases"]}, proc.returncode


def run_inspect(rows: list, log_dir: Path):
    """Harness B: the independent Inspect AI implementation."""
    try:
        actual = importlib.metadata.version("inspect-ai")
    except importlib.metadata.PackageNotFoundError as exc:
        raise H1NotExecuted(
            "inspect-ai is not installed. Run: "
            f"{sys.executable} -m pip install inspect-ai=={EXPECTED_INSPECT_VERSION}"
        ) from exc
    if actual != EXPECTED_INSPECT_VERSION:
        raise H1NotExecuted(
            f"Inspect version mismatch: expected {EXPECTED_INSPECT_VERSION}, "
            f"got {actual}"
        )

    sys.path.insert(0, str(HERE))
    try:
        from inspect_ai import eval as inspect_eval
        from inspect_harness import make_task
    except Exception as exc:
        raise H1NotExecuted(
            f"could not load the Inspect harness: {type(exc).__name__}: {exc}"
        ) from exc

    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True)

    try:
        logs = inspect_eval(
            make_task(rows), model=None, log_dir=str(log_dir), display="plain"
        )
    except Exception as exc:
        raise H1NotExecuted(
            f"Inspect evaluation failed: {type(exc).__name__}: {exc}"
        ) from exc

    if not logs:
        raise H1NotExecuted("Inspect returned no EvalLog")
    log = logs[0]

    results = {}
    for sample in log.samples or []:
        if not sample.scores:
            raise H1NotExecuted(f"Inspect sample {sample.id} has no scores")
        score = next(iter(sample.scores.values()))
        value = score.text
        if value not in RESULT_VOCABULARY:
            raise H1NotExecuted(
                f"Inspect sample {sample.id} produced {value!r}, which is "
                "outside the ICTS result vocabulary"
            )
        results[str(sample.id)] = value
    return results, actual


def build_comparisons(rows, bare, insp):
    """Case-by-case ledger. No aggregate-only comparison."""
    expected_by_id = {r["case_id"]: r["expected"] for r in rows}
    comparisons = []
    for cid in sorted(set(expected_by_id) | set(bare) | set(insp)):
        expected = expected_by_id.get(cid)
        b = bare.get(cid)
        i = insp.get(cid)
        comparisons.append(
            {
                "case_id": cid,
                "expected": expected,
                "bare_python_result": b,
                "inspect_ai_result": i,
                "equivalent": bool(expected is not None and b == i == expected),
            }
        )
    return comparisons


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the ICTS H1 harness-independence gate."
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--frozen-tree",
        metavar="REPO_ROOT",
        help="Repository root carrying the verified frozen v0.1.2 inputs.",
    )
    src.add_argument(
        "--frozen-zip",
        metavar="ZIP",
        help="Path to the frozen ICTS v0.1.2 ZIP.",
    )
    parser.add_argument(
        "--output",
        default=str(HERE / "H1_RESULT.json"),
        help="Where to write the H1 result artifact.",
    )
    parser.add_argument(
        "--independence-output",
        default=str(HERE / "H1_INDEPENDENCE_RECORD.json"),
        help="Where to write the independence record.",
    )
    args = parser.parse_args()

    started = datetime.now(timezone.utc).isoformat()
    repo_commit = None
    inspect_version = None
    bare_exit = None
    inspect_exit = None
    independence = None

    try:
        independence = check_independence()
        Path(args.independence_output).write_text(
            json.dumps(independence, indent=2, sort_keys=True) + "\n"
        )
        print(
            "OK: independence record written "
            f"(independent={independence['independent']})"
        )
        if not independence["independent"]:
            raise H1NotExecuted(
                "Inspect harness is not independent of the bare-Python "
                "implementation; H1 would be meaningless."
            )

        with tempfile.TemporaryDirectory(prefix="icts_h1_") as td:
            workdir = Path(td)

            if args.frozen_tree:
                repo_root = Path(args.frozen_tree).resolve()
                vroot = frozen_tree_from_repo(repo_root, workdir)
                repo_commit = git_commit(repo_root)
            else:
                vroot = frozen_tree_from_zip(Path(args.frozen_zip).resolve(), workdir)
                repo_commit = git_commit(HERE)

            rows = load_case_rows(vroot)
            print(f"OK: loaded {len(rows)} frozen cases")

            bare, bare_exit = run_bare_python(vroot)
            print(f"OK: bare-Python harness produced {len(bare)} results")

            insp, inspect_version = run_inspect(rows, HERE / "inspect_logs")
            inspect_exit = 0
            print(f"OK: Inspect harness produced {len(insp)} results")

        comparisons = build_comparisons(rows, bare, insp)
        terminal = (
            "H1_PASS"
            if comparisons and all(c["equivalent"] for c in comparisons)
            else "H1_FAIL"
        )

    except H1NotExecuted as exc:
        print(f"H1_NOT_EXECUTED: {exc}", file=sys.stderr)
        result = {
            "gate": "H1",
            "h1_version": H1_VERSION,
            "icts_version": ICTS_VERSION,
            "terminal": "H1_NOT_EXECUTED",
            "reason": str(exc),
            "independence_check": independence,
            "run_metadata": {
                "generated_at_utc": started,
                "python_version": platform.python_version(),
                "platform": platform.platform(),
            },
        }
        Path(args.output).write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n"
        )
        return 2

    # The normative portion: everything the gate's verdict depends on. It holds
    # no timestamps, no paths and nothing environment-specific, so it is stable
    # across machines and runs and can be compared digest-to-digest.
    normative = {
        "gate": "H1",
        "icts_version": ICTS_VERSION,
        "h1_version": H1_VERSION,
        "vector": VECTOR,
        "property": PROPERTY,
        "normative_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "comparisons": comparisons,
        "terminal": terminal,
    }
    normative_sha = hashlib.sha256(
        json.dumps(normative, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    result = dict(normative)
    result.update(
        {
            "inspect_ai_version": inspect_version,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "repo_commit": repo_commit,
            "bare_python_exit": bare_exit,
            "inspect_exit": inspect_exit,
            "independence_check": independence,
            "cases_total": len(comparisons),
            "cases_equivalent": sum(1 for c in comparisons if c["equivalent"]),
            "normative_comparison_sha256": normative_sha,
            # Run metadata is deliberately separated from the normative portion.
            # The whole file is NOT byte-reproducible across environments; the
            # normative portion and its digest are.
            "run_metadata": {
                "generated_at_utc": started,
                "input_mode": "frozen-tree" if args.frozen_tree else "frozen-zip",
            },
            "claim": (
                "H1 established for ICTS-VEC-EXT-EVIDENCE-001: the frozen vector "
                "produced identical normative terminal results across the "
                "bare-Python and Inspect AI reference implementations. This does "
                "not establish full ICTS harness independence, all properties, "
                "H2, field validity, field EPSR, vendor conformance, or "
                "deployment certification."
                if terminal == "H1_PASS"
                else "Harness equivalence not established."
            ),
        }
    )

    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print()
    header = f"{'case':<6} {'expected':<24} {'bare_python':<24} {'inspect_ai':<24} ok"
    print(header)
    print("-" * len(header))
    for c in comparisons:
        print(
            f"{c['case_id']:<6} {str(c['expected']):<24} "
            f"{str(c['bare_python_result']):<24} {str(c['inspect_ai_result']):<24} "
            f"{'yes' if c['equivalent'] else 'NO'}"
        )
    print()
    print(f"cases                        {result['cases_total']}")
    print(f"equivalent                   {result['cases_equivalent']}")
    print(f"normative_comparison_sha256  {normative_sha}")
    print(f"terminal                     {terminal}")

    return 0 if terminal == "H1_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
