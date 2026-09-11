# Architecture

## What ICTS is

ICTS is a neutral executable test suite that asks whether institutional properties survived
execution across an assembled deployment.

It is **not** an authority layer, a policy engine, an observability product, an agent-control
plane, a governance dashboard, a generic LLM benchmark, or a cloud scanner. It does not sit in
the request path and it does not decide anything at runtime. It reads evidence after the fact
and adjudicates.

> Veraxis defines the test. The institution runs the test. The institution owns the evidence.

## The problem it addresses

An institution does not deploy a model. It assembles a system: models, agents, memory,
retrieval, identity, tools, policy engines, and external evidence sources, from several
vendors, wired together in a configuration nobody vendor-tested.

Each vendor can describe what its component is designed to do. None of them can tell you what
the assembled system did. Component-level assurance does not compose, and the gaps between
components are exactly where institutional controls fail.

ICTS tests the assembly.

## Pipeline

```
deployment
+ configuration
+ frozen test vector
+ admitted observations
        |
        v
provenance-constrained normalization
        |
        v
Evidence Sufficiency Contract
        |
        v
invariant adjudication
        |
        v
PASS
FAIL
NOT_TESTABLE
NOT_APPLICABLE_TOPOLOGY
INVALID_TEST_EXECUTION
```

### Inputs

- **Deployment and configuration** — the system as actually assembled.
- **Frozen test vector** — pins the property, required observation types, topology rules, and
  result vocabulary. Frozen so that a result means the same thing across runs and across
  institutions.
- **Frozen deployment topology declaration** — declares the domains and their relationship.
  Topology applicability comes from this declaration, never inferred from telemetry.
- **Admitted observations** — native events emitted by the deployment, mapped by a local
  adapter.

### Stage 1 — provenance-constrained normalization

Native events are normalized under the Normalization Provenance Contract. Every normative
value carries `source_observation_id`, `source_field`, and `transform`, and is verified at
runtime against the native source.

This stage runs before anything normative is read, so an untraceable value never reaches a
predicate. See [`evidence-model.md`](evidence-model.md).

### Stage 2 — topology eligibility

The frozen topology declaration determines whether the deployment can structurally instantiate
the property at all. A single-domain deployment cannot exhibit cross-domain external-evidence
reliance, so the property does not apply: `NOT_APPLICABLE_TOPOLOGY`.

This is a positive structural statement. Absent telemetry never produces it.

### Stage 3 — Evidence Sufficiency Contract

The ESC asks a single question: **are the admitted observations sufficient to adjudicate?**

If no frozen evidence path is satisfiable, the result is `NOT_TESTABLE`. The property applies;
the evidence does not reach.

### Stage 4 — invariant adjudication

Only if evidence is sufficient does the invariant predicate run, yielding `PASS` or `FAIL`.

At any stage, an integrity failure — malformed events, duplicate singletons, mapper insertion
or omission, broken provenance — yields `INVALID_TEST_EXECUTION`. A broken test is reported as
a broken test, never as a conformance answer.

## The two-predicate rule

> **Evidence sufficiency establishes adjudicability. It does not establish conformance.**

Sufficiency and conformance are separate predicates specified in separate artifacts. A suite
that collapses them punishes observability gaps instead of testing controls: every blind spot
becomes a violation, institutions learn to instrument less, and the results stop meaning
anything.

## Source independence

> **The source of evidence must not be allowed to define the conditions under which that
> evidence counts.**

If the originating source can establish its own acceptance conditions, external evidence
becomes self-authorizing and the property is vacuous. ICTS enforces this mechanically: an
acceptance condition whose `established_by_domain` is the originating evidence domain does not
count. An independently administered third declared domain may establish it.

## Neutrality

`spec/core/` must not depend on Authority VM, OIC, VEIP, ZTL, Veraxis product terminology, a
model vendor, a policy engine, or an observability vendor. A property that cannot be stated
without one of those is not a core property.

ICTS does not require adoption of Authority VM or any other architecture. Authority VM
conformance, if adopted later, may use these same neutral properties as a stricter conformance
profile.

## Result binding

A result is meaningless unless it names what produced it. Every run bundle binds the manifest
digest, per-artifact digests for property/NPC/ESC/vector/cases, per-case fixture and topology
digests, and the execution environment.

A result applies to **one deployment, one configuration, one vector, one evidence set**. There
is no result in the vocabulary that says a vendor globally passes ICTS.

## Replaceability

`reference/` is replaceable. The specification is the product; the implementation is an
existence proof. A third party must be able to implement `spec/` independently — that is what
the H1 gate exists to test.
