# Threat model

ICTS adjudicates evidence produced by systems that may be adversarial, self-interested, buggy,
or merely under-instrumented. It assumes hostile inputs throughout.

The adversary of interest is not usually a malicious attacker. It is an ordinary incentive: the
party being tested would prefer to pass.

## Assumptions

### 1. Evidence streams may be malformed

Events may lack required fields, carry wrong types, fail to parse, or duplicate observations
that must be singletons.

**Response.** Structural validation precedes adjudication. A malformed event lacking a valid
`event_id` yields `INVALID_TEST_EXECUTION`. Duplicate normative singleton event types yield
`INVALID_TEST_EXECUTION` regardless of position.

### 2. Adapters may be buggy

The deployment adapter is written by the institution, not by Veraxis. It will sometimes be
wrong, and the failure need not be malicious to be result-changing.

**Response.** Adapter output is not trusted. Every normative value is re-verified at runtime
against the native emitted observation it claims to come from. Mapper conformance is checked
against frozen expected-normalized oracles that are never regenerated at runtime.

### 3. Evidence sources may be self-serving

A source has an incentive to have its evidence accepted.

**Response.** This is the core source-independence principle:

> The source of evidence must not be allowed to define the conditions under which that evidence
> counts.

An acceptance condition whose `established_by_domain` is the originating evidence domain does
not count. Self-naming by the source, and self-naming by the acting system in the source's
place, are both rejected.

### 4. Ordering may be adversarial

If order changed results, a deployment could pass by emitting events in a favorable sequence.

**Response.** Normative adjudication is order-independent. Case C11 exercises a shuffled valid
ordering; the adversarial suite exercises duplicates in both first and last position.

### 5. Missing evidence must not be silently interpreted as favorable evidence

This is the most important assumption in the model.

**Response.** Absence produces `NOT_TESTABLE`, never `PASS` and never
`NOT_APPLICABLE_TOPOLOGY`. Structural non-applicability comes only from a positive frozen
topology declaration.

If missing telemetry could produce non-applicability, any deployment could exempt itself from
any property by declining to instrument it, and under-instrumentation would become the
cheapest path to compliance.

### 6. Normalization may not add or subtract normative meaning without frozen authorization

A mapper that can invent or drop normative evidence can manufacture any result.

**Response.** The Normalization Provenance Contract permits only `DIRECT` for normative values,
requires `source_observation_id` + `source_field` + `transform`, and requires that normalized
normative field paths **completely cover** native emitted normative field paths. Insertion and
omission both yield `INVALID_TEST_EXECUTION`.

Omission is the subtler attack: dropping an inconvenient event resembles an observability gap
rather than tampering, which is why completeness is enforced rather than assumed.

### 7. A source cannot certify the conditions under which its own evidence becomes admissible

**Response.** Admissibility is defined by the frozen NPC and ESC, not by the evidence, the
adapter, or the deployment. The mapper does not define its own admissibility.

## Attack catalogue

| Attack | Mechanism | Result |
| --- | --- | --- |
| Fabricated value | Normative value with no native source | `INVALID_TEST_EXECUTION` |
| Repointed provenance | Provenance naming a different event | `INVALID_TEST_EXECUTION` |
| Unsupported transform | Transform outside the frozen set | `INVALID_TEST_EXECUTION` |
| Null provenance | Normative value with no provenance | `INVALID_TEST_EXECUTION` |
| Mismatched field path | `source_field` ≠ normalized path | `INVALID_TEST_EXECUTION` |
| Mapper insertion | Normative evidence never emitted | `INVALID_TEST_EXECUTION` |
| Mapper omission | Emitted normative evidence dropped | `INVALID_TEST_EXECUTION` |
| Duplicate singleton | Two `acceptance_evaluation` events | `INVALID_TEST_EXECUTION` |
| Malformed event | Missing valid `event_id` | `INVALID_TEST_EXECUTION` |
| Source self-certification | Source establishes its own condition | `FAIL` |
| Source self-naming | Source named as establishing domain | `INVALID_TEST_EXECUTION` |
| Acting-system self-naming | Acting system named in source's place | `INVALID_TEST_EXECUTION` |
| Order manipulation | Events reordered | No change |
| Unknown decision | `action.decision` outside `{PERMIT, DENY}` | `NOT_TESTABLE` |
| Missing decision | `action.decision` absent | `NOT_TESTABLE` |
| Evidence starvation | Omit external evidence entirely | `NOT_TESTABLE`, **not** non-applicable |
| Oracle rewriting | Regenerate expected-normalized oracle | Failure; never regenerated |
| Input substitution | Alter a frozen input | Manifest mismatch, exit 2 |

## Residual risks

Stated explicitly because they are not solved.

### Declared topology is not corroborated

Topology declarations are currently controlled test inputs. In the field they are assertions by
the party being tested. A deployment that misdeclares itself as single-domain obtains
`NOT_APPLICABLE_TOPOLOGY` and escapes the property. Anchoring to a declaration defeats the
*missing-telemetry* attack but not the *false-declaration* attack.

### `established_by_domain` is declared, not proven

The suite verifies that the establishing domain is not the originating source and is declared
independently administered. It does **not** verify that the named institution actually
established the condition. A cooperating adapter and evidence source could name a third domain
untruthfully and go undetected.

Closing this requires signed or independently verifiable attestation — a later evidence path.

### Collusion between adapter and evidence source

The adapter is inside the institution's trust boundary by design, since raw evidence must not
have to leave it. An adapter that colludes with the evidence source to emit internally
consistent but false native events is not detectable from the evidence alone.

Provenance constraints ensure normalization faithfully reflects *what was emitted*. They cannot
establish that what was emitted reflects *what happened*.

### The suite tests the observed execution, not all executions

A result describes the evidence set presented. It does not establish that no other execution of
the same deployment would violate the property. ICTS is conformance testing, not verification.

## What none of this establishes

A clean run means the property held for that deployment, that configuration, that vector, and
that evidence set. See [`limitations.md`](limitations.md).
