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

The helpers below (verify_frozen_files, materialize_frozen_package) are also
imported by reference/inspect_ai/run_h1.py so that the H1 gate runs against the
same verified frozen inputs, through one implementation rather than two.

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

FROZEN_PACKAGE_DIRNAME = "icts_v0_c18_synthetic_first_v0.1.2"


class FrozenPackageError(RuntimeError):
    """Raised when the repository's frozen v0.1.2 inputs do not verify."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def repo_path_for(manifest_rel: str) -> Path:
    return REPO / DISPLACED.get(manifest_rel, manifest_rel)


def verify_frozen_files():
    """Verify the frozen manifest and every file it lists.

    Returns (manifest, manifest_sha256, problems). `problems` is empty when the
    repository's frozen inputs are intact.
    """
    problems = []

    manifest_file = REPO / "MANIFEST.json"
    if not manifest_file.exists():
        return None, None, ["MANIFEST.json is missing from the repository root"]

    manifest_sha = sha256_file(manifest_file)
    if manifest_sha != EXPECTED_MANIFEST_SHA256:
        problems.append(
            "frozen MANIFEST.json digest mismatch\n"
            f"    expected {EXPECTED_MANIFEST_SHA256}\n"
            f"    observed {manifest_sha}"
        )

    provenance_manifest = REPO / "provenance" / "v0.1.2-manifest.json"
    if not provenance_manifest.exists():
        problems.append("provenance/v0.1.2-manifest.json is missing")
    elif sha256_file(provenance_manifest) != manifest_sha:
        problems.append(
            "provenance/v0.1.2-manifest.json has drifted from MANIFEST.json"
        )

    manifest = json.loads(manifest_file.read_text())
    for rel, meta in sorted(manifest["files"].items()):
        target = repo_path_for(rel)
        if not target.exists():
            problems.append(
                f"missing: {rel} (expected at {target.relative_to(REPO)})"
            )
            continue
        observed = sha256_file(target)
        if observed != meta["sha256"]:
            problems.append(
                f"altered: {rel}\n"
                f"    expected {meta['sha256']}\n"
                f"    observed {observed}"
            )

    return manifest, manifest_sha, problems


def materialize_frozen_package(dest_parent: Path) -> Path:
    """Reconstitute the exact frozen v0.1.2 package under `dest_parent`.

    Verifies every frozen file first and raises FrozenPackageError if anything
    is missing or altered. Restores the displaced README.md to its frozen bytes
    so the resulting tree is manifest-clean to the unmodified run_suite.py.

    Returns the package root.
    """
    manifest, _manifest_sha, problems = verify_frozen_files()
    if problems:
        raise FrozenPackageError(
            "frozen inputs did not verify:\n  " + "\n  ".join(problems)
        )

    vroot = Path(dest_parent) / FROZEN_PACKAGE_DIRNAME
    vroot.mkdir(parents=True, exist_ok=True)

    shutil.copy2(REPO / "MANIFEST.json", vroot / "MANIFEST.json")
    for rel in manifest["files"]:
        dest = vroot / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(repo_path_for(rel), dest)

    return vroot


def run_frozen_suite(vroot: Path):
    """Run the UNMODIFIED frozen run_suite.py inside a materialized package."""
    proc = subprocess.run(
        [sys.executable, "reference/bare_python/run_suite.py"],
        cwd=vroot,
        text=True,
        capture_output=True,
    )
    return proc


def main() -> int:
    manifest, manifest_sha, problems = verify_frozen_files()
    if problems:
        print(f"FAIL: {len(problems)} frozen file problem(s) found")
        for p in problems:
            print("  " + p)
        return 1

    print(f"OK: frozen MANIFEST.json digest {manifest_sha}")
    print(
        f"OK: all {len(manifest['files'])} frozen manifest entries "
        "verified byte-for-byte"
    )
    for rel, mapped in DISPLACED.items():
        print(f"    (documented port deviation: {rel} carried at {mapped})")

    # Reconstitute the exact frozen package and run the unmodified suite in it.
    with tempfile.TemporaryDirectory(prefix="icts_frozen_") as td:
        vroot = materialize_frozen_package(Path(td))
        proc = run_frozen_suite(vroot)
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
