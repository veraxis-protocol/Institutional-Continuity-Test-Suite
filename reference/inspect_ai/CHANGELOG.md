# ICTS H1 Inspect harness — changelog

This changelog covers the **second harness** (`ICTS_H1_INSPECT_*`) only. It is
non-normative and versioned independently of ICTS itself. No entry here changes
ICTS v0.1.2 normative semantics.

## v0.1.1

First version to actually execute the H1 gate.

**Result:** `H1_PASS` — 14/14 frozen cases equivalent.
Evidence: [`H1_RESULT.json`](H1_RESULT.json),
[`H1_INDEPENDENCE_RECORD.json`](H1_INDEPENDENCE_RECORD.json).

### Changed

- **Repaired Inspect scorer API compatibility with `inspect-ai==0.3.263`.**
  `@scorer` → `@scorer(metrics=[])`. `metrics` is a required parameter of
  `scorer(...)`; the bare decorator in v0.1.0 passed the decorated function as
  `metrics` and left `scorer_type` unbound. An empty sequence is the API-correct
  minimum: ICTS terminal results are categorical, not correct/incorrect, so no
  aggregate metric is meaningful, and H1 compares results case by case.
  **Scoring semantics are unchanged.**

- **Added reproducible frozen-tree/ZIP input handling.** `run_h1.py` now takes
  exactly one explicit input mode and never searches any directory implicitly:

  ```
  python reference/inspect_ai/run_h1.py --frozen-tree .
  python reference/inspect_ai/run_h1.py --frozen-zip /path/to/v0.1.2.zip
  ```

  Tree mode runs the full v0.1.2 integrity gate first (all 42 frozen manifest
  entries verified byte-for-byte), then reconstitutes the exact frozen package.
  ZIP mode verifies the archive SHA-256 before extraction. Both then verify the
  frozen manifest digest, so they converge on the same frozen normative inputs.
  Frozen-package verification is not weakened in either mode.

### Added

- **Case-by-case equivalence evidence.** `H1_RESULT.json` records
  `case_id / expected / bare_python_result / inspect_ai_result / equivalent` for
  every frozen case. No aggregate-only comparison is used. The normative portion
  carries no timestamps or environment data and is digested separately as
  `normative_comparison_sha256`; the file as a whole is not byte-reproducible
  and is not claimed to be.

- **Mechanical implementation-independence check.** `H1_INDEPENDENCE_RECORD.json`
  is populated by static AST and textual inspection of `inspect_harness.py` plus
  runtime module-ownership checks after import — not by assumption.

- **Explicit terminal states.** `H1_PASS` (exit 0), `H1_FAIL` (exit 1),
  `H1_NOT_EXECUTED` (exit 2). An execution or environment failure is never
  converted into a pass.

- **H1 as a required-success CI job** on Python 3.11 and 3.12. It is no longer
  `continue-on-error`.

### Preserved

- All ICTS v0.1.2 normative semantics. `spec/`, `synthetic/`,
  `reference/bare_python/`, `MANIFEST.json`, `provenance/v0.1.2-README.md` and
  `CHANGELOG_v0.1.2.md` are untouched and still verify byte-for-byte.

## v0.1.0

**Did not execute against its own Inspect pin.**

The harness declared its scorer with a bare decorator:

```python
@scorer
def icts_c18_scorer():
```

Under its own pinned `inspect-ai==0.3.263`, `metrics` is a required parameter of
`scorer(...)`, so the bare decorator passed the decorated function as `metrics`
and left `scorer_type` unbound. Importing the task raised:

```
TypeError: scorer.<locals>.wrapper() missing 1 required positional argument: 'scorer_type'
```

`run_h1.py` additionally required the frozen v0.1.2 ZIP to sit beside it, which
made H1 unrunnable from the public repository.

Consequently H1 was **not established** for v0.1.0, and the repository carried
`H1 EXECUTION PENDING`.

This defect is retained here deliberately. The version that failed to execute
against its own pin is part of the record, and v0.1.0 history is not rewritten.

One contributing factor is worth recording alongside the defect: the H1 CI job
was advisory (`continue-on-error`), so a harness that could not even import
produced no failing signal. In v0.1.1 the job is a required-success gate.
