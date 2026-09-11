# Writing a deployment adapter

A deployment adapter maps your system's native telemetry into the native emitted observation
shape ICTS adjudicates. It runs **inside your environment**. Raw evidence does not have to
leave your boundary.

> **Status.** This describes the current evidence contract, which is exercised today against
> frozen synthetic fixtures. Adapters for real deployments are not yet supported end to end;
> there is no adapter SDK and no `icts run`. See
> [`limitations.md`](limitations.md).

## The deployment model

1. You download or vendor the versioned suite.
2. You run it inside your own environment.
3. Your adapter maps native evidence locally.
4. Raw evidence remains inside your boundary by default.
5. The evaluator returns a configuration-bound result plus reproducibility evidence.
6. You may optionally share a result/evidence bundle.

Steps 3 and 4 are the reason the adapter is yours and not ours.

## What the adapter must produce

A native observation set: the events your deployment actually emitted, in ICTS event shape.

```json
{
  "fixture_id": "YOUR_RUN_ID",
  "events": [
    {
      "event_id": "E1",
      "type": "external_evidence",
      "evidence_id": "EXT-123",
      "source_domain": "DOMAIN_A",
      "target_domain": "DOMAIN_B",
      "claim": "counterparty_status=eligible"
    },
    {
      "event_id": "E2",
      "type": "acceptance_policy",
      "acting_domain": "DOMAIN_B",
      "policy_id": "POL-B-7",
      "required_conditions": ["signature_valid", "issuer_allowed", "freshness_valid"]
    },
    {
      "event_id": "E3",
      "type": "acceptance_evaluation",
      "acting_domain": "DOMAIN_B",
      "evidence_id": "EXT-123",
      "condition_results": {
        "signature_valid": { "value": true, "established_by_domain": "DOMAIN_B" },
        "issuer_allowed":  { "value": true, "established_by_domain": "DOMAIN_B" },
        "freshness_valid": { "value": true, "established_by_domain": "DOMAIN_B" }
      }
    },
    {
      "event_id": "E4",
      "type": "action",
      "acting_domain": "DOMAIN_B",
      "decision": "PERMIT",
      "used_evidence_id": "EXT-123",
      "parent_event_id": "E3"
    }
  ]
}
```

For `ICTS-VEC-EXT-EVIDENCE-001`, each of the four types must appear **exactly once**. Every
event needs a unique, valid `event_id`.

Correlation is explicit, never inferred:

- `acceptance_evaluation.evidence_id` == `external_evidence.evidence_id`
- `action.used_evidence_id` == `external_evidence.evidence_id`
- `action.parent_event_id` == `acceptance_evaluation.event_id`
- `acceptance_policy.acting_domain` == `external_evidence.target_domain`

## The frozen topology declaration

Separate from evidence, and **not** derived from telemetry:

```json
{
  "artifact_id": "YOUR-TOPOLOGY-001",
  "deployment_id": "YOUR-DEPLOYMENT-001",
  "domains": [
    { "domain_id": "DOMAIN_A", "administration": "independent" },
    { "domain_id": "DOMAIN_B", "administration": "independent" }
  ],
  "relationship": {
    "external_evidence_relationship": true,
    "cross_domain": true,
    "evidence_origin": "DOMAIN_A",
    "acting_system": "DOMAIN_B"
  },
  "causal_model": "explicit_event_parent_links",
  "wall_clock_required_for_normative_adjudication": false,
  "version": "0.1.2"
}
```

It is frozen before the run. Declaring it afterwards, from what the telemetry happened to
show, defeats the point: topology eligibility would collapse back into observability.

Note the residual risk: a topology declaration is an assertion by the party being tested. See
[`threat-model.md`](threat-model.md).

## Rules the adapter must obey

### Map, do not interpret

Every normative value must trace directly to a native emitted field under `DIRECT`: the
normalized value equals the value at `source_field` in the event identified by
`source_observation_id`, and the normalized path equals `source_field`.

Forbidden for normative fields: `inference`, `default_filling`, `alias_resolution`,
`semantic_scope_parsing`, `identifier_equivalence_guessing`, `timestamp_synthesis`,
`correlation_inference`.

If your telemetry needs any of those to produce a normative value, that value is **not
admissible**. Emit it as `derived_diagnostic` instead, and treat the gap as an instrumentation
finding.

### Do not add

Never synthesize an event or field the deployment did not emit. Filling a gap to make the suite
adjudicable produces `INVALID_TEST_EXECUTION`, which is correct: a manufactured `PASS` would be
worse than an honest `NOT_TESTABLE`.

### Do not subtract

Never drop emitted normative evidence. Normalized normative field paths must completely cover
native emitted normative field paths. Omission produces `INVALID_TEST_EXECUTION`.

### Do not let the source establish its own conditions

`established_by_domain` must name the domain that actually established the condition. It must
not be the originating evidence domain. The acting domain may establish; an independently
administered third declared domain may establish.

### Keep diagnostics separate

Normative evidence goes in `observations`. Everything derived goes in `derived_diagnostic`, and
can never satisfy a normative predicate.

## Common outcomes

| You see | Cause | Fix |
| --- | --- | --- |
| `NOT_TESTABLE` | ESC path unsatisfied | Instrument the missing observation or field — do not fabricate it |
| `NOT_APPLICABLE_TOPOLOGY` | Topology cannot instantiate the property | Nothing to fix; confirm the declaration is truthful |
| `INVALID_TEST_EXECUTION` | Provenance, completeness, duplicate, or malformed event | Read `details`; fix the adapter |
| `FAIL` | Invariant violated | A real finding about the deployment |

`NOT_TESTABLE` is a normal early result. It means "instrument this", not "you failed". Treat
the path from `NOT_TESTABLE` to an adjudicable result as evidence-coverage work.

## Validating your adapter

Before trusting it, run it against the frozen synthetic fixtures and confirm you reproduce the
expected results in `synthetic/cases.json`. An adapter that cannot reproduce the frozen cases
will not produce trustworthy results on your deployment.

Then check the adversarial properties on your own mapping: shuffle event order and confirm the
result is unchanged; drop a normative field and confirm you get `INVALID_TEST_EXECUTION` rather
than a quiet `NOT_TESTABLE`.

## Result scope

A result applies to **one deployment, one configuration, one vector, one evidence set**. It does
not generalize to your organization, your vendor, or your next configuration.
