# Security and trust model

ICTS adjudicates evidence about systems that may be adversarial, buggy, self-interested, or
simply broken. The suite is therefore written to assume that its inputs are hostile.

The full analysis is in [`docs/threat-model.md`](docs/threat-model.md). This file states the
assumptions and the reporting process.

## Assumptions ICTS must make

ICTS assumes all of the following at all times:

- **Evidence streams may be malformed.** Events may be missing fields, carry wrong types,
  duplicate singleton observations, or fail to parse.
- **Adapters may be buggy.** A deployment adapter is written by the institution, not by
  Veraxis, and may map native evidence incorrectly.
- **Evidence sources may be self-serving.** A source has an incentive to have its own
  evidence accepted.
- **Ordering may be adversarial.** Event order must not change a normative result.
- **Missing evidence must not be silently interpreted as favorable evidence.** Absence is
  `NOT_TESTABLE`, never `PASS` and never `NOT_APPLICABLE_TOPOLOGY`.
- **Normalization may not add or subtract normative meaning without frozen authorization.**
  A mapper that inserts or omits normative evidence produces `INVALID_TEST_EXECUTION`.
- **A source cannot certify the conditions under which its own evidence becomes admissible.**

That last assumption is the core source-independence principle:

> The source of evidence must not be allowed to define the conditions under which that
> evidence counts.

## What this means for results

- Insufficient evidence never becomes `FAIL`. It becomes `NOT_TESTABLE`.
- Malformed or unsupported evidence never becomes `PASS`. It becomes
  `INVALID_TEST_EXECUTION` or `NOT_TESTABLE`.
- Structural non-applicability comes only from a positive frozen topology declaration, never
  from absent telemetry.
- Every result is bound to the exact hashes of the inputs that produced it.

## Handling evidence safely

Evidence bundles can contain sensitive institutional data.

- Raw evidence stays inside the customer boundary by default. ICTS is designed so that
  running the suite never requires sending production data to Veraxis.
- Do not commit run output. `evidence/` is generated on every run and is gitignored.
- Before sharing any bundle, review it. A run bundle contains fixture hashes, environment
  details, and adjudication detail strings.
- Never commit credentials, API keys, tokens, internal hostnames, or absolute local paths to
  this repository.

## Reporting a security issue

Report suspected security issues, evidence-integrity defects, or ways to obtain an unearned
`PASS` privately to **security@veraxis.io**. Please do not open a public issue first.

Useful reports include the exact package version and manifest digest, the inputs, the
observed result, the expected result, and why the difference matters.

A finding that changes a normative result, admits fabricated evidence, bypasses provenance,
changes a result through input ordering, or confuses topology with observability is treated
as blocking.

Security-relevant proposals follow the same disposition commitments as any other external
change — see [`governance/EXTERNAL_CHANGE_PROCESS.md`](governance/EXTERNAL_CHANGE_PROCESS.md).
Silence is never the implicit status.
