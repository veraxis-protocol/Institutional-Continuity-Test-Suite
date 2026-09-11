# Contributing

ICTS is a conformance test suite. Its value depends on results being reproducible and on
frozen artifacts staying frozen, so contribution rules are stricter than in an ordinary
codebase.

## The two rules that matter most

1. **Do not change frozen artifacts.** Every file listed in `MANIFEST.json` is carried
   byte-for-byte from the frozen v0.1.2 package and is verified by CI. If you change one,
   CI fails, and that is the intended behavior.
2. **Semantic changes require a new version.** A change to what a result means, when evidence
   is sufficient, or how normalization is constrained is never a patch to an existing
   version. It enters a future version through the process below.

## Proposing a change to the specification

Specification, vector, Evidence Sufficiency Contract, and Normalization Provenance Contract
changes go through the external change process:

`PROPOSE -> TRIAGE -> REPRODUCE -> ACCEPT | REJECT | DEFER`

- `TRIAGE_TARGET` — 14 calendar days from receipt.
- `DISPOSITION_TARGET` — 45 calendar days from receipt.
- Missed targets are recorded as `OVERDUE_TRIAGE` or `OVERDUE_DISPOSITION`.
- Silence is never the implicit status.

See [`governance/EXTERNAL_CHANGE_PROCESS.md`](governance/EXTERNAL_CHANGE_PROCESS.md) for the
full commitments, and [`governance/REVIEW_POLICY.md`](governance/REVIEW_POLICY.md) for how
review independence is handled.

## What makes a good report

The strongest contribution is a reproduction, not an opinion. Include:

- the package version and the `MANIFEST.json` digest you tested;
- the exact command, Python version, and platform;
- the inputs, ideally as a minimal fixture;
- expected result, observed result, and why the difference matters;
- whether you consider it blocking.

Separate the class of defect: specification, implementation, fixture, evidence bundle,
documentation mismatch, or non-blocking observation. These have different dispositions.

## Adding a synthetic case

Synthetic cases are frozen inputs, not test scratch space.

- Fixtures live in `synthetic/fixtures/`, topologies in `synthetic/topologies/`.
- Every fixture needs a frozen expected-normalized oracle in
  `synthetic/expected_normalized/`. Oracles are inputs. They are **never** regenerated at
  runtime, and a missing oracle is a failure rather than a prompt to create one.
- Register the case in `synthetic/cases.json` with its expected result.
- New cases belong to a new version, because `MANIFEST.json` pins the current set.

Do not describe synthetic case counts as EPSR. The synthetic metric is
`synthetic_case_adjudicability`. Field EPSR is `FIELD_EPSR_PENDING`.

## Reference implementations

`reference/` is explicitly replaceable. Reference implementation behavior must not become the
specification by accident: if the code and `spec/` disagree, that is a defect worth
reporting, and the resolution is to state the intended semantics in `spec/` rather than to
document the code's behavior after the fact.

Independent implementations are welcome and are the point of the project.

## Before you open a pull request

```bash
python scripts/verify_frozen_package.py
python reference/bare_python/run_adversarial_regression.py
```

Both must exit 0. CI runs the same commands on every supported Python version.

Also check that you have not committed generated run output (`evidence/`), `__pycache__`,
`.pyc` files, credentials, tokens, or absolute local paths.

## Code style

The reference implementation is deliberately bare Python with no third-party dependencies, so
that it can be read and re-implemented without a toolchain. Keep it that way. Optional
harnesses may take dependencies, but the core suite must never depend on them.

## Conduct

Review is adversarial by design. Attack the artifact, not the person. Red findings are
preserved rather than quietly resolved — see
[`review/BLIND_REVIEW_PROTOCOL.md`](review/BLIND_REVIEW_PROTOCOL.md).
