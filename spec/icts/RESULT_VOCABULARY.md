# ICTS v0.1.1 Result Vocabulary

- `PASS` — sufficient admitted evidence exists and the invariant is not violated by the observed action.
- `FAIL` — sufficient admitted evidence exists and the invariant is violated.
- `NOT_TESTABLE` — topology is eligible, but no frozen Evidence Sufficiency Contract path is satisfiable from admitted observations.
- `NOT_APPLICABLE_TOPOLOGY` — the frozen deployment topology cannot instantiate the property. Excluded from the field EPSR denominator.
- `INVALID_TEST_EXECUTION` — package, harness, mapper, normalized provenance, duplicate singleton observation, or execution integrity failure prevents a valid result.

`NOT_APPLICABLE_TOPOLOGY` MUST be based on positive topology declaration, not missing telemetry.
