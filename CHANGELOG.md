# Changelog

This file records changes to the **public repository**. It does not rewrite the history of
any frozen ICTS package.

Frozen package changelogs are preserved verbatim alongside the package they describe. For
v0.1.2 see [`CHANGELOG_v0.1.2.md`](CHANGELOG_v0.1.2.md).

Accepted changes enter future versions only. Historical conformance evidence is never
rewritten.

## Unreleased

Nothing.

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
