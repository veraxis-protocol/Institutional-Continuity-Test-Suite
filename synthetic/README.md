# Synthetic deployment

Frozen synthetic inputs for the C18-derived vector. These are **normative inputs**: they are
pinned in `MANIFEST.json` and verified on every run.

**Synthetic cases are not deployments.** Nothing in this directory is field evidence, and no
count derived from it is an EPSR.

## Layout

| Path | Role |
| --- | --- |
| `cases.json` | The case list: fixture, topology, and expected result per case |
| `fixtures/` | Native emitted observation sets |
| `topologies/` | Frozen deployment topology declarations |
| `expected_normalized/` | Frozen expected-normalized oracles |

## Oracles are inputs, not output

`expected_normalized/` holds frozen oracles for the mapper conformance check. They are
**never regenerated at runtime**. A missing oracle is a failure, not a prompt to create one.

This matters: an oracle that a harness can regenerate is not a conformance reference, because
a broken mapper would simply rewrite its own answer key.

The one exception is `invalid_missing_event_id_001.json`, which has no oracle by design —
normalization is required to *reject* it, so a normalized form would be meaningless.

## Cases

| Case | Fixture | Topology | Expected |
| --- | --- | --- | --- |
| C01 | `valid_permit_001` | two_domain | `PASS` |
| C02 | `not_testable_missing_condition_001` | two_domain | `NOT_TESTABLE` |
| C03 | `fail_source_self_certifies_001` | two_domain | `FAIL` |
| C04 | `not_testable_missing_correlation_001` | two_domain | `NOT_TESTABLE` |
| C05 | `fail_observed_false_condition_001` | two_domain | `FAIL` |
| C06 | `valid_deny_001` | two_domain | `PASS` |
| C07 | `not_testable_unknown_decision_001` | two_domain | `NOT_TESTABLE` |
| C08 | `not_testable_missing_decision_001` | two_domain | `NOT_TESTABLE` |
| C09 | `not_testable_missing_external_event_001` | two_domain | `NOT_TESTABLE` |
| C10 | `invalid_duplicate_evaluation_001` | two_domain | `INVALID_TEST_EXECUTION` |
| C11 | `valid_order_shuffled_001` | two_domain | `PASS` |
| C12 | `valid_third_party_establishment_001` | three_domain | `PASS` |
| C13 | `invalid_missing_event_id_001` | two_domain | `INVALID_TEST_EXECUTION` |
| C14 | `not_applicable_single_domain_001` | single_domain | `NOT_APPLICABLE_TOPOLOGY` |

What the interesting cases are actually testing:

- **C03 — source self-certification.** The originating evidence domain establishes its own
  acceptance condition. This is the central attack the property exists to catch.
- **C05 vs C02 — false versus absent.** An observed `false` condition is `FAIL`. An absent
  condition result is `NOT_TESTABLE`. Absence is not evidence of violation.
- **C09 vs C14 — evidence versus topology.** A missing external observation on an eligible
  topology is `NOT_TESTABLE`. A single-domain topology that structurally cannot instantiate
  the property is `NOT_APPLICABLE_TOPOLOGY`. Missing telemetry must never become structural
  non-applicability.
- **C11 — ordering.** Shuffled event order must not change the result.
- **C12 — third-party establishment.** An independently administered third declared domain
  may establish an acceptance condition, where the originating source may not.
- **C07 / C08 — closed decision enumeration.** An unknown or missing `action.decision`
  cannot produce `PASS`.

## The synthetic metric

The metric computed over this directory is:

```
synthetic_case_adjudicability = k / n
```

where `n` counts topology-eligible, structurally valid synthetic cases and `k` counts those
that reached `PASS` or `FAIL`. The current suite reports `k=6, n=11`.

This is **not** an EPSR and **not** a deployment metric. Field EPSR is defined in the vector
over topology-eligible *deployments* and its status is:

```
FIELD_EPSR_PENDING
```

Do not describe synthetic case counts as field EPSR.
