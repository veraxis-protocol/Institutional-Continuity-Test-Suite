# Evidence model

How raw deployment output becomes evidence that ICTS will adjudicate, and what it is not
allowed to become on the way.

## Two namespaces

| Namespace | Role |
| --- | --- |
| `observations` | **Normative.** May satisfy predicates. |
| `derived_diagnostic` | Diagnostic only. May **never** satisfy a normative predicate. |

Keeping derivation separate from normative evidence is the whole point. Anything inferred,
guessed, defaulted, or reconstructed is diagnostic, and diagnostic values cannot make a
property pass.

## Native emitted observations

A native observation set is the deployment's own output. For
`ICTS-VEC-EXT-EVIDENCE-001` the required singleton event types are:

| Type | Carries |
| --- | --- |
| `external_evidence` | `evidence_id`, `source_domain`, `target_domain` |
| `acceptance_policy` | `policy_id`, `acting_domain`, `required_conditions` |
| `acceptance_evaluation` | `evidence_id`, `condition_results` |
| `action` | `decision`, `used_evidence_id`, `parent_event_id` |

Every event needs a valid `event_id` and `type`. Each of these types must appear **exactly
once**; a duplicate is `INVALID_TEST_EXECUTION`, not a tie to be broken.

## Normalization Provenance Contract

Normalization is where a conformance suite is most easily defeated: a mapper that can invent,
repoint, or drop a value can manufacture any result. So normalization is constrained and the
constraint is checked at runtime.

### The current normative transform

```
DIRECT
```

Under `DIRECT`, the normalized value must **equal** the value at `source_field` in the native
event identified by `source_observation_id`, and the normalized field path must equal
`source_field`.

Every normative value is wrapped with its provenance:

```json
{
  "source_observation_id": "E1",
  "source_field": "source_domain",
  "transform": "DIRECT",
  "value": "DOMAIN_A"
}
```

### Runtime validation

Each wrapped normative value is checked:

- the transform is permitted;
- `source_observation_id` resolves to exactly one native event;
- `source_field` resolves in that event;
- the normalized value equals the resolved native value exactly;
- for `DIRECT`, the normalized field path equals `source_field`;
- diagnostic values cannot satisfy normative predicates;
- normalized normative field paths **completely cover** native emitted normative field paths,
  excluding only explicitly frozen diagnostic-only exclusions.

### What is rejected

The implementation rejects all of:

- **fabricated values** — a value with no native source;
- **repointed provenance** — provenance naming a different event than the value came from;
- **unsupported transforms** — anything outside the frozen set;
- **null provenance** — a normative value with no provenance;
- **mismatched field paths** — `source_field` not matching the normalized path;
- **mapper insertion** — normative evidence that the deployment never emitted;
- **mapper subtraction** — emitted normative evidence silently dropped.

Insertion and subtraction are both checked. Subtraction is the subtler attack: a mapper that
drops an inconvenient event makes a deployment look cleaner than it is, and without a
completeness rule it looks like an observability gap.

### Forbidden for normative fields

`inference`, `default_filling`, `alias_resolution`, `semantic_scope_parsing`,
`identifier_equivalence_guessing`, `timestamp_synthesis`, `correlation_inference`.

If a normative field cannot be directly and mechanically traced to a native emitted
observation, it is **inadmissible**.

> **The mapper does not define its own admissibility.** The frozen NPC does.

## Evidence Sufficiency Contract

The ESC determines whether evidence is sufficient to adjudicate. It does **not** determine
whether the property passes. It is published separately from invariant adjudication so the two
cannot quietly merge.

### Path EA-1

External evidence + acceptance policy + acceptance evaluation + causally linked action.
Sufficiency requires **all** of:

- exactly one `external_evidence`, with `evidence_id`, `source_domain`, `target_domain`;
- exactly one `acceptance_policy`, with `policy_id`, and
  `acting_domain == external_evidence.target_domain`;
- `required_conditions` is a non-empty list;
- exactly one `acceptance_evaluation`, with
  `evidence_id == external_evidence.evidence_id`;
- `condition_results` covers **every** required condition;
- every required condition result carries a **boolean** `value` and an
  `established_by_domain`;
- exactly one `action`, with `used_evidence_id == external_evidence.evidence_id` and
  `parent_event_id == acceptance_evaluation.event_id`;
- `action.decision` present and in the closed enumeration `{PERMIT, DENY}`.

`sufficient_when: EA-1 == true`.

These requirements are exactly what the code enforces. Contract/code drift is a reportable
defect.

### Decision semantics

| `action.decision` | Meaning |
| --- | --- |
| `PERMIT` | The property is exercised; the invariant must evaluate all required acceptance conditions. |
| `DENY` | No authorization occurred from the external evidence; that action does not violate the property. |
| other or missing | The evidence path is unsatisfied and **must not** produce `PASS`. |

A closed enumeration matters: an open one lets an unrecognized decision drift toward the
permissive default, and an unknown decision is the exact circumstance in which a suite should
decline to answer.

## Invariant adjudication

Only once evidence is sufficient does the invariant run. The property fails if externally
originating evidence changed the permitted action set while a required acceptance condition
was:

- **absent** — but note: absent from `condition_results` is a *sufficiency* failure
  (`NOT_TESTABLE`), not a violation;
- **unsatisfied** — observed `false` → `FAIL`;
- **unverifiable** from an admitted evidence path;
- **established only by the originating source itself** → `FAIL`.

The distinction between an observed `false` and an absent result is the difference between
`FAIL` and `NOT_TESTABLE`, and it is deliberate. Not knowing is not the same as knowing it
went wrong.

## Establishment and independence

Each condition result carries `established_by_domain`. The rule:

- the **originating evidence domain** may not establish its own acceptance conditions;
- the **acting domain** may;
- an **independently administered third declared domain** may.

Domain independence comes from the frozen topology declaration, where each domain carries an
`administration` field.

### A limitation worth stating plainly

`established_by_domain` is a **declared** identity under the current synthetic evidence model.
It is not cryptographic proof that the named institution actually established the condition.
Nothing here yet prevents a cooperating adapter from naming a third domain untruthfully.

Stronger establishment requires a later evidence path such as signed or independently
verifiable attestation. See [`limitations.md`](limitations.md).

## Result binding

Every run bundle binds the manifest digest, per-artifact spec digests, per-case fixture and
topology digests, the environment, the command, and a UTC timestamp — so a result names
exactly the inputs that produced it.
