# Running locally

## Requirements

- Python 3.9 or newer.
- No third-party dependencies for the core suite.

The core conformance suite is deliberately dependency-free so it can run inside a restricted
institutional environment without a package install.

## The commands that work today

```bash
git clone https://github.com/veraxis-protocol/institutional-continuity-test-suite
cd institutional-continuity-test-suite

# 1. Frozen-package integrity gate + ordinary suite
python scripts/verify_frozen_package.py

# 2. Adversarial regression suite
python reference/bare_python/run_adversarial_regression.py
```

Both must exit 0.

### Expected output

`scripts/verify_frozen_package.py`:

```
OK: frozen MANIFEST.json digest 920d390714cc9593cf0a79c1caf80f2566419e2fa05d6e12cb9c403b20f0040f
OK: all 42 frozen manifest entries verified byte-for-byte
OK: reconstituted frozen package ran clean
    terminal                      PASS
    cases                         14
    failures                      0
    mapper_conformance.passed     True
    field_epsr                    FIELD_EPSR_PENDING
    synthetic_case_adjudicability k=6 n=11 (NOT field EPSR)
```

`run_adversarial_regression.py` prints a JSON bundle with 15 checks and `"terminal": "PASS"`.

## Why the suite runs through the integrity gate

`reference/bare_python/run_suite.py` verifies `MANIFEST.json` against files resolved relative
to its own package root. This repository's root `README.md` is the public product README,
while the frozen v0.1.2 `README.md` is preserved at `provenance/v0.1.2-README.md`.

So running:

```bash
python reference/bare_python/run_suite.py
```

directly from the repository root exits **2** with a manifest error for `README.md`. That is
the integrity check working correctly, not a defect — and it was preferred over editing the
frozen code or the frozen manifest to accommodate a directory layout.

`scripts/verify_frozen_package.py` resolves this without touching anything frozen: it verifies
all 42 manifest hashes, reconstitutes the exact frozen package in a temporary directory with
`README.md` restored to its frozen bytes, then runs the **unmodified** `run_suite.py` inside
it.

To run the frozen suite by hand exactly as shipped, extract the frozen v0.1.2 package into its
own directory and run `python reference/bare_python/run_suite.py` from that package root.

## Reading the run bundle

A run writes `evidence/run_result.json` (gitignored — it is generated output, never a frozen
input). Key fields:

| Field | Meaning |
| --- | --- |
| `terminal` | `PASS` only if no case failed and mapper conformance held |
| `manifest_sha256` | Digest of the frozen manifest the run was bound to |
| `bound_artifacts` | Digests of property, NPC, ESC, vector, cases |
| `cases[]` | Per case: expected, observed, evidence path, details, fixture and topology digests |
| `mapper_conformance` | Whether normalization matched every frozen oracle |
| `synthetic_case_adjudicability` | `k`/`n` — **not** an EPSR |
| `field_epsr` | `FIELD_EPSR_PENDING` |
| `environment` | Python version, implementation, platform |

The bundle binds the exact inputs that produced it, so a result can be reproduced or disputed
precisely.

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Terminal `PASS` |
| 1 | A case result differed from expectation, or mapper conformance failed |
| 2 | Manifest verification failed — inputs are not what they claim to be |

## Second harness (H1)

Optional, under development, and **not** part of the core gate.

```bash
python -m pip install -r reference/inspect_ai/requirements.txt   # inspect-ai==0.3.263
python reference/inspect_ai/run_h1.py
```

This does **not** currently run to completion. `run_h1.py` requires the frozen v0.1.2 ZIP
beside it, and the harness does not load under its own pin. Both blockers, and the current
`H1 EXECUTION PENDING` status, are documented in
[`../reference/inspect_ai/README.md`](../reference/inspect_ai/README.md).

An unavailable optional harness must never make the core suite unusable, which is why H1 is a
separate non-blocking CI job.

## The intended end-user interface

The eventual product interaction is:

```
icts inspect     # discover deployment topology and evidence availability
icts run         # execute the frozen vectors against the deployment
icts report      # emit a configuration-bound result and evidence bundle
```

**None of these commands exist yet.** Nothing in this repository implements them. They are
stated so the intended shape is clear, not to imply available functionality.

## Running against a real deployment

Not yet possible from this repository. The current release adjudicates frozen synthetic
fixtures. Running against a real deployment requires a deployment adapter that maps native
evidence under the Normalization Provenance Contract — see
[`writing-an-adapter.md`](writing-an-adapter.md) — and the claim ceilings in
[`limitations.md`](limitations.md) apply.

## Troubleshooting

**Exit 2, manifest mismatch.** A frozen file was modified. Check `git status`. Frozen files
are not editable in place; a semantic change requires a new version.

**`frozen expected-normalized oracle missing`.** An oracle is a frozen input. It is never
regenerated at runtime — restore it rather than creating one.

**`INVALID_TEST_EXECUTION` on your own fixture.** Normalization rejected it. The `details`
field names the cause: fabricated value, repointed provenance, unsupported transform, mapper
omission, duplicate singleton, or a missing `event_id`.
