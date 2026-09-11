"""Frozen-package integrity gate for the ported ICTS v0.1.2 repository.

NON-NORMATIVE. This script is repository infrastructure, not part of the
specification and not part of the frozen v0.1.2 reference implementation.
It does not adjudicate anything and it never modifies the frozen files.

Why this exists
---------------
This repository is SEMANTICALLY PORTED FROM FROZEN v0.1.2. Every file listed
in the frozen MANIFEST.json is carried here byte-for-byte, at its original
manifest path, with exactly one documented exception:

    README.md  ->  provenance/v0.1.2-README.md

The repository root README.md is the public, product-facing README required of
a canonical public repository. The frozen v0.1.2 README.md is preserved,
unmodified, at provenance/v0.1.2-README.md.

The frozen reference implementation (reference/bare_python/run_suite.py)
verifies MANIFEST.json against files resolved relative to its own package root.
Because of the one displaced file above, it cannot be run directly from the
repository root without reporting a manifest error -- which is the integrity
check behaving correctly, not a defect.

Rather than modify the frozen v0.1.2 code or the frozen manifest, this script
reconstitutes the exact frozen package in a temporary directory from the files
in this repository, restores README.md to its frozen bytes, and then executes
the UNMODIFIED run_suite.py inside it.

That makes this script simultaneously:
  1. a byte-level integrity check of all 42 frozen manifest entries, and
  2. proof that this repository still carries a runnable, manifest-clean
     copy of frozen v0.1.2.

Exit codes
----------
0  all frozen hashes matched and the frozen suite returned terminal PASS
1  a frozen file is missing, altered, or the frozen suite did not pass
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# The single documented port deviation: frozen manifest path -> repository path.
DISPLACED = {"README.md": "provenance/v0.1.2-README.md"}

EXPECTED_MANIFEST_SHA256 = (
    "920d390714cc9593cf0a79c1caf80f2566419e2fa05d6e12cb9c403b20f0040f"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repo_path_for(manifest_rel: str) -> Path:
    return REPO / DISPLACED.get(manifest_rel, manifest_rel)


def main() -> int:
    manifest_file = REPO / "MANIFEST.json"
    if not manifest_file.exists():
        print("FAIL: MANIFEST.json is missing from the repository root")
        return 1

    manifest_sha = sha256_bytes(manifest_file.read_bytes())
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        print("FAIL: frozen MANIFEST.json digest mismatch")
        print(f"  expected {EXPECTED_MANIFEST_SHA256}")
        print(f"  observed {manifest_sha}")
        return 1

    # The provenance copy must stay identical to the root manifest.
    provenance_manifest = REPO / "provenance" / "v0.1.2-manifest.json"
    if not provenance_manifest.exists():
        print("FAIL: provenance/v0.1.2-manifest.json is missing")
        return 1
    if sha256_bytes(provenance_manifest.read_bytes()) != manifest_sha:
        print("FAIL: provenance/v0.1.2-manifest.json has drifted from MANIFEST.json")
        return 1

    manifest = json.loads(manifest_file.read_text())
    files = manifest["files"]

    problems = []
    for rel, meta in sorted(files.items()):
        target = repo_path_for(rel)
        if not target.exists():
            problems.append(f"missing: {rel} (expected at {target.relative_to(REPO)})")
            continue
        observed = sha256_bytes(target.read_bytes())
        if observed != meta["sha256"]:
            problems.append(
                f"altered: {rel}\n    expected {meta['sha256']}\n    observed {observed}"
            )

    if problems:
        print(f"FAIL: {len(problems)} frozen file problem(s) found")
        for p in problems:
            print("  " + p)
        return 1

    print(f"OK: frozen MANIFEST.json digest {manifest_sha}")
    print(f"OK: all {len(files)} frozen manifest entries verified byte-for-byte")
    for rel, mapped in DISPLACED.items():
        print(f"    (documented port deviation: {rel} carried at {mapped})")

    # Reconstitute the exact frozen package and run the unmodified suite in it.
    with tempfile.TemporaryDirectory(prefix="icts_frozen_") as td:
        vroot = Path(td) / "icts_v0_c18_synthetic_first_v0.1.2"
        vroot.mkdir(parents=True)

        shutil.copy2(manifest_file, vroot / "MANIFEST.json")
        for rel in files:
            dest = vroot / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(repo_path_for(rel), dest)

        proc = subprocess.run(
            [sys.executable, "reference/bare_python/run_suite.py"],
            cwd=vroot,
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            print("FAIL: frozen suite did not exit 0 inside the reconstituted package")
            print(proc.stdout[-4000:])
            print(proc.stderr[-4000:])
            return 1

        bundle = json.loads(proc.stdout)

    if bundle.get("terminal") != "PASS":
        print(f"FAIL: frozen suite terminal was {bundle.get('terminal')!r}")
        return 1
    if bundle.get("manifest_sha256") != EXPECTED_MANIFEST_SHA256:
        print("FAIL: frozen suite did not bind the expected manifest digest")
        return 1

    print("OK: reconstituted frozen package ran clean")
    print(f"    terminal                      {bundle['terminal']}")
    print(f"    manifest_sha256               {bundle['manifest_sha256']}")
    print(f"    cases                         {len(bundle['cases'])}")
    print(f"    failures                      {len(bundle['failures'])}")
    print(f"    mapper_conformance.passed     {bundle['mapper_conformance']['passed']}")
    print(f"    field_epsr                    {bundle['field_epsr']}")
    sca = bundle["synthetic_case_adjudicability"]
    print(f"    synthetic_case_adjudicability k={sca['k']} n={sca['n']} (NOT field EPSR)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
