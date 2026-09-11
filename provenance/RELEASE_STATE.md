# Release state

What this repository is, what it was built from, and exactly how strong the provenance claim
is.

## Source version

| Field | Value |
| --- | --- |
| Source artifact | `ICTS_v0_C18_SYNTHETIC_FIRST_v0.1.2` |
| Version | `0.1.2` |
| Manifest `artifact` id | `ICTS-C18-SYNTHETIC-FIRST-v0.1.2` |
| Manifest generated at | `2026-09-11T03:45:36.426845+00:00` |
| Hash algorithm | SHA-256 |
| Manifest entries | 42 |
| Second harness package | `ICTS_H1_INSPECT_v0.1.0` |

## Digests

**Frozen source ZIP**

```
a3f225bd493f297d340688345a686f16cd16df14cf39676621e1d6232b2d070b
```

**Frozen internal `MANIFEST.json`**

```
920d390714cc9593cf0a79c1caf80f2566419e2fa05d6e12cb9c403b20f0040f
```

The manifest digest is recomputed on every CI run by `scripts/verify_frozen_package.py`, and
is also emitted as `manifest_sha256` in every run bundle.

### Exactly what was verified, and what was not

This distinction matters and is stated precisely rather than rounded up.

**Verified directly:**

- The frozen `MANIFEST.json` carried in this repository hashes to
  `920d390714cc9593cf0a79c1caf80f2566419e2fa05d6e12cb9c403b20f0040f`, matching the declared
  frozen manifest digest.
- All **42** files listed in that manifest are present in this repository and each matches its
  declared SHA-256 **byte-for-byte**.
- The frozen suite, reconstituted from these files, runs clean and binds the expected manifest
  digest.

**Not verified directly:**

- The **frozen ZIP digest above was not recomputed in the environment that populated this
  repository.** The ZIP was not retrievable there, so the repository was populated from the
  archive's extracted contents and each extracted file was verified individually against the
  frozen manifest.
- The ZIP digest is therefore **declared, and corroborated** by the independent
  `ICTS_H1_INSPECT_v0.1.0` manifest, which records the same value for the embedded v0.1.2
  archive. It is not an independent recomputation.

Per-file verification against the frozen manifest is a finer-grained check of *content* than
the ZIP digest, which additionally covers archive packaging (compression parameters, entry
order, timestamps). Anyone holding the ZIP should recompute its digest independently.

## Relationship between this repository and the frozen package

```
SEMANTICALLY PORTED FROM FROZEN v0.1.2
```

This repository is **not** byte-identical to the frozen ZIP as an archive, and no such claim
is made. It is a reorganized public repository that carries every frozen file byte-for-byte.

### What is carried byte-for-byte

All 42 manifest-listed files, at their original manifest paths:

- `spec/core/CORE-PROP-EXT-EVIDENCE-001.md`
- `spec/icts/` — vector, ESC, NPC, result vocabulary
- `synthetic/` — `cases.json`, fixtures, topologies, expected-normalized oracles
- `reference/bare_python/` — `icts_core.py`, `run_suite.py`, `run_adversarial_regression.py`
- `governance/EXTERNAL_CHANGE_PROCESS.md`
- `CHANGELOG_v0.1.2.md`
- `MANIFEST.json`

The `ICTS_H1_INSPECT_v0.1.0` files in `reference/inspect_ai/` are likewise carried
byte-for-byte and verified against that package's own manifest.

### The one documented port deviation

| Frozen manifest path | Carried in this repository at |
| --- | --- |
| `README.md` | `provenance/v0.1.2-README.md` |

The repository root `README.md` is the public, product-facing README that a canonical public
repository requires. The frozen v0.1.2 `README.md` is preserved unmodified at
`provenance/v0.1.2-README.md`.

`scripts/verify_frozen_package.py` resolves this mapping explicitly, verifies all 42 hashes,
then reconstitutes the exact frozen package in a temporary directory — restoring `README.md`
to its frozen bytes — and runs the **unmodified** `run_suite.py` inside it. No frozen file and
no frozen digest was edited to accommodate the layout.

`provenance/v0.1.2-manifest.json` is a byte-identical copy of the root `MANIFEST.json`; CI
fails if the two ever drift.

### What was added

New, clearly non-normative repository material: the root `README.md`, `docs/`, `review/`,
`governance/REVIEW_POLICY.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`,
`LICENSE-PENDING.md`, `pyproject.toml`, `.gitignore`, `scripts/`, directory READMEs, and the
CI workflow.

None of it is executed by the frozen reference implementation, and none of it can change an
adjudication outcome.

### What was deliberately not changed

Two non-blocking patches proposed during Session 002 review of v0.1.2 were **not** applied:

1. Rejecting a reserved `derived_diagnostic` field name on native events in `icts_core.py`.
2. Adding a `normative_digest` to the run bundle in `run_suite.py`.

This repository must first represent the reviewed candidate faithfully. Improvements become a
separately versioned change, not a silent edit to a candidate under review.

## Reproducing

```bash
python scripts/verify_frozen_package.py
python reference/bare_python/run_adversarial_regression.py
```

Both exit 0. The first prints the frozen manifest digest and confirms all 42 entries.

Expected frozen suite output: terminal `PASS`, 14 cases, 0 failures,
`mapper_conformance.passed = true`, `field_epsr = FIELD_EPSR_PENDING`,
`synthetic_case_adjudicability k=6 n=11`.

Expected adversarial output: terminal `PASS`, 15 checks.

## Claim ceilings

**Established**

- One neutral external-evidence property has an executable specification.
- Bare-Python reference implementation exists.
- Provenance-constrained normalization is load-bearing.
- Mapper addition and subtraction attacks are checked.
- Topology identity is anchored to the frozen topology declaration.
- Topology ineligibility is distinct from observability failure.
- Deterministic synthetic cases execute.
- Adversarial regression suite passes locally.
- `FIELD_EPSR_PENDING`.
- Synthetic case ratios are not field EPSR.

**Not established**

- Blind independent review gate.
- H1 harness independence — `H1 EXECUTION PENDING`.
- H2.
- Field usefulness.
- Live bank deployment.
- Field EPSR.
- Actual cryptographic proof that `established_by_domain` corresponds to the real establishing
  institution.
- Generalized five-vector v0 conformance.

See [`../docs/limitations.md`](../docs/limitations.md).
