# Bare-Python reference implementation

The v0.1.2 reference implementation, carried byte-for-byte from the frozen
`ICTS_v0_C18_SYNTHETIC_FIRST_v0.1.2` package.

**This is not the specification.** It is one implementation of
[`../../spec/`](../../spec/), and it is replaceable. If this code and the specification
disagree, that is a defect worth reporting.

## Files

| File | Role |
| --- | --- |
| `icts_core.py` | Normalization, provenance validation, Evidence Sufficiency Contract evaluation, invariant adjudication |
| `run_suite.py` | Runs the 14 frozen synthetic cases, verifies the manifest, emits a run bundle |
| `run_adversarial_regression.py` | Runs 15 adversarial regression checks |

No third-party dependencies. Python 3.9+.

## Running

```bash
# From the repository root:
python scripts/verify_frozen_package.py
python reference/bare_python/run_adversarial_regression.py
```

Both must exit 0.

`run_suite.py` is invoked through `scripts/verify_frozen_package.py` rather than directly.
The reason is a deliberate, documented consequence of how this repository is laid out:
`run_suite.py` verifies `MANIFEST.json` against its own package root, and the repository root
`README.md` is the public product README rather than the frozen v0.1.2 README (preserved at
[`../../provenance/v0.1.2-README.md`](../../provenance/v0.1.2-README.md)). Running
`run_suite.py` straight from the repository root therefore reports a manifest error for that
one file — which is the integrity check working correctly.

`scripts/verify_frozen_package.py` resolves this without editing frozen code: it reconstitutes
the exact frozen package in a temporary directory from this repository's files, restores
`README.md` to its frozen bytes, and runs this **unmodified** `run_suite.py` inside it. See
[`../../docs/running-locally.md`](../../docs/running-locally.md).

## What the suite binds

Every run bundle binds the exact inputs that produced it:

- `manifest_sha256`, and per-artifact digests for the property, NPC, ESC, vector, and cases;
- per-case fixture and topology digests;
- Python version, implementation, platform, command, and UTC timestamp.

A result that is not bound to its inputs is not reproducible evidence, so the binding is part
of the output rather than a convenience.

Run output is written to `evidence/run_result.json`. It is generated on every run, is
environment-bound, and is gitignored — it must never be committed as if it were a frozen
input.

## Architecture

```
native emitted observations
        |
        v  provenance-constrained DIRECT normalization  (NPC)
        v  runtime provenance verification against native source
        |
        v  frozen topology declaration            -> NOT_APPLICABLE_TOPOLOGY
        |
        v  Evidence Sufficiency Contract  (ESC)   -> NOT_TESTABLE
        |
        v  invariant adjudication                 -> PASS | FAIL
        |
        (integrity failure at any stage)          -> INVALID_TEST_EXECUTION
```

Normalization is load-bearing and runs before anything normative is read. A normative value
that cannot be traced to `source_observation_id` + `source_field` under a permitted
`transform` is inadmissible.

## Adversarial regression

`run_adversarial_regression.py` covers 15 checks, including:

- fabricated values, fabricated transforms, and null provenance;
- mapper omission of emitted normative evidence;
- duplicate singleton events in first and last position;
- missing external evidence returning `NOT_TESTABLE` rather than a topology verdict;
- unknown and missing `action.decision` being unable to produce `PASS`;
- event-order independence;
- source self-naming and acting-system self-naming rejection;
- third-party establishment being allowed where self-establishment is not.

These are regression guards for defects that would otherwise silently return an unearned
result. They are not a substitute for independent adversarial review.

## Do not modify

Every file here is pinned in `MANIFEST.json` and verified on every CI run. A semantic change
requires a new version through
[`../../governance/EXTERNAL_CHANGE_PROCESS.md`](../../governance/EXTERNAL_CHANGE_PROCESS.md).
