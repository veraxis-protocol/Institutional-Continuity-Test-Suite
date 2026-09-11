# ICTS C18 Synthetic-First v0.1.2 — Surgical Repair

This release preserves the v0.1.0 neutral property and architecture while repairing implementation defects identified in the v0.1.0 technical audit.

Resolved targets:

- F-01: all normative sufficiency/adjudication reads now consume normalized observations.
- F-02: `action.decision` is required by the ESC and restricted to `PERMIT|DENY`; missing/unknown values cannot PASS.
- F-03: duplicate normative singleton event types deterministically produce `INVALID_TEST_EXECUTION`.
- F-04: topology applicability comes from a frozen deployment topology declaration, not missing telemetry.
- F-05: all normative inputs, cases, fixtures, topologies, expected-normalized oracles, specs, and executable source are manifest-hashed.
- F-06: expected-normalized oracles are frozen inputs; a missing oracle is a failure and is never regenerated at runtime.
- F-07: ESC field names use `evidence_id` consistently.
- F-08: an independently administered third declared domain may establish an acceptance condition; the originating evidence domain may not.
- F-09: the synthetic metric is renamed `synthetic_case_adjudicability`; field EPSR remains pending.
- F-10: the observed-false case is a frozen fixture.
- F-11: run evidence binds exact manifest/spec/vector/case/fixture/topology hashes plus environment, command, and timestamp.
- F-12/F-13: clean transcript generation and no `__pycache__`/`.pyc` files in package.
- F-14: missing-condition fixture renamed as `not_testable_*`.

Claim ceiling remains: H1 harness independence is NOT established. v0.1.2 contains only the bare-Python reference implementation.
