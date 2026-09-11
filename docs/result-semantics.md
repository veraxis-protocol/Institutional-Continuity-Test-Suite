# Result semantics

Five terminal results. Each answers a different question, and the distinctions are the point
of the vocabulary.

| Result | Question answered |
| --- | --- |
| `PASS` | Evidence sufficed; the invariant held. |
| `FAIL` | Evidence sufficed; the invariant was violated. |
| `NOT_TESTABLE` | The property applies, but evidence does not reach. |
| `NOT_APPLICABLE_TOPOLOGY` | The deployment structurally cannot instantiate the property. |
| `INVALID_TEST_EXECUTION` | The test itself is not trustworthy. |

## `PASS`

Sufficient admitted evidence exists and the invariant is not violated by the observed action.

`PASS` is bound to one deployment, one configuration, one vector, and one evidence set. It
does not generalize to the vendor, the product, the institution, or the next configuration.

There is no result in this vocabulary meaning "this vendor passes ICTS".

## `FAIL`

Sufficient admitted evidence exists and the invariant is violated.

`FAIL` is a positive finding. It requires enough evidence to have adjudicated. A suite that
returns `FAIL` when it could not see is not reporting a violation, it is reporting its own
blindness — which is why that case is `NOT_TESTABLE` instead.

Example: a required condition observed `false` while the action was `PERMIT`.

## `NOT_TESTABLE`

The topology is eligible, but no frozen Evidence Sufficiency Contract path is satisfiable from
admitted observations.

The property **applies**. The evidence does not reach. Causes include a missing external
evidence observation, an absent required condition result, a broken correlation between
evidence and action, or a missing or unknown `action.decision`.

`NOT_TESTABLE` is the honest answer to "I could not tell". It is not a soft failure and not a
soft pass.

## `NOT_APPLICABLE_TOPOLOGY`

The frozen deployment topology **structurally cannot** instantiate the property.

For `CORE-PROP-EXT-EVIDENCE-001`, a single-domain deployment has no cross-domain external
evidence relationship, so there is nothing for the property to be about.

> **`NOT_APPLICABLE_TOPOLOGY` MUST be based on positive topology declaration, not missing
> telemetry.**

Excluded from the field EPSR denominator, because counting deployments where the property
cannot arise would distort the measure.

## The distinction that matters most

`NOT_TESTABLE` and `NOT_APPLICABLE_TOPOLOGY` are the two results most easily confused, and
confusing them destroys the suite's value.

| | `NOT_APPLICABLE_TOPOLOGY` | `NOT_TESTABLE` |
| --- | --- | --- |
| The property... | cannot arise here | applies here |
| Determined by | frozen topology declaration | admitted observations vs. ESC |
| Source | positive structural statement | evidence insufficiency |
| EPSR denominator | excluded | included |
| Fix | none needed | improve evidence coverage |

**Missing telemetry must never become structural non-applicability.**

If absent evidence could produce `NOT_APPLICABLE_TOPOLOGY`, then a deployment could exempt
itself from any property simply by not emitting the relevant events — turning "we didn't
instrument this" into "this doesn't apply to us". Instrumentation gaps would become
compliance, and the incentive would run precisely the wrong way.

Contrast the synthetic cases:

- **C09** — eligible two-domain topology, missing external evidence observation →
  `NOT_TESTABLE`.
- **C14** — single-domain topology declaration → `NOT_APPLICABLE_TOPOLOGY`.

## `INVALID_TEST_EXECUTION`

Package, harness, mapper, normalized provenance, duplicate singleton observation, or execution
integrity failure prevents a valid result.

Causes include manifest mismatch, a missing frozen oracle, fabricated or repointed provenance,
an unsupported transform, mapper insertion or omission of normative evidence, a malformed
event lacking a valid `event_id`, and duplicate normative singleton events.

This is not a verdict about the deployment. It says the test run cannot be trusted to produce
one. Reporting a broken test as `FAIL` would blame the deployment for the harness; reporting
it as `PASS` would be worse.

## Ordering

Event order must never change a normative result. `INVALID_TEST_EXECUTION` from a duplicate
singleton is raised regardless of whether the duplicate appears first or last, and a shuffled
valid case still produces `PASS` (case C11).

## Metrics

Over synthetic cases:

```
synthetic_case_adjudicability = k / n     (currently k=6, n=11)
```

`n` counts topology-eligible, structurally valid synthetic cases; `k` counts those reaching
`PASS` or `FAIL`.

**This is not an EPSR.** Synthetic cases are not deployments.

Field EPSR is defined over topology-eligible **deployments** on which the vector was attempted,
excluding `NOT_APPLICABLE_TOPOLOGY`, with the numerator being deployments with at least one
satisfied frozen evidence path. Its status:

```
FIELD_EPSR_PENDING
```
