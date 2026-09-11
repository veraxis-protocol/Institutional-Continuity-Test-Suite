# Changelog

This file records changes to the **public repository**. It does not rewrite the history of
any frozen ICTS package.

Frozen package changelogs are preserved verbatim alongside the package they describe. For
v0.1.2 see [`CHANGELOG_v0.1.2.md`](CHANGELOG_v0.1.2.md).

Accepted changes enter future versions only. Historical conformance evidence is never
rewritten.

## Unreleased

### H1 harness independence established for EXT-EVIDENCE-001

Second harness repaired and the H1 gate executed. See
[`reference/inspect_ai/CHANGELOG.md`](reference/inspect_ai/CHANGELOG.md) for the harness
changelog, including the preserved v0.1.0 defect.

- `ICTS_H1_INSPECT_v0.1.1` repairs Inspect scorer API compatibility with
  `inspect-ai==0.3.263` and replaces the fragile ZIP-location dependency with explicit
  `--frozen-tree` / `--frozen-zip` input modes.
- H1 executed: **`H1_PASS`**, 14/14 frozen cases equivalent across the bare-Python and
  Inspect AI implementations.
- Added committed evidence (`H1_RESULT.json`) and a mechanical independence record
  (`H1_INDEPENDENCE_RECORD.json`).
- H1 CI is now a required-success job on Python 3.11 and 3.12, no longer `continue-on-error`.

No ICTS v0.1.2 normative artifact changed. The two Session 002 non-blocking patches remain
deliberately unapplied.

## Repository bootstrap — v0.1.2 port

Initial population of the canonical public repository from the frozen
`ICTS_v0_C18_SYNTHETIC_FIRST_v0.1.2` package.

### Added

- `spec/core/CORE-PROP-EXT-EVIDENCE-001.md` — the first architecture-neutral property.
- `spec/icts/` — vector, Evidence Sufficiency Contract, Normalization Provenance Contract,
  and result vocabulary.
- `synthetic/` — frozen topologies, fixtures, expected-normalized oracles, and case list.
- `reference/bare_python/` — the v0.1.2 reference implementation and adversarial regression.
- `reference/inspect_ai/` — the ICTS_H1_INSPECT v0.1.0 second-harness package, as frozen.
- `governance/`, `review/`, `docs/`, `provenance/` — process and explanatory material.
- `scripts/verify_frozen_package.py` — repository integrity gate.
- GitHub Actions workflow running the integrity gate and the adversarial regression.

### Semantics

No v0.1.2 semantics were changed. The specification, the reference implementation, and all
frozen inputs are carried byte-for-byte and are verified on every CI run.

### Deliberately not applied

Two non-blocking patches proposed during Claude Session 002 review of v0.1.2 were **not**
applied:

1. Rejecting a reserved `derived_diagnostic` field name on native events in `icts_core.py`.
2. Adding a `normative_digest` to the run bundle in `run_suite.py`.

Both are plausible improvements. Neither is applied here, because this repository must first
represent the reviewed candidate faithfully. They are candidates for a later version through
the process in [`governance/EXTERNAL_CHANGE_PROCESS.md`](governance/EXTERNAL_CHANGE_PROCESS.md),
not silent edits to a candidate under review.

### Licensing

No licence designated. See [`LICENSE-PENDING.md`](LICENSE-PENDING.md).
