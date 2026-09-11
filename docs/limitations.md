# Limitations

This page exists so that nobody has to reverse-engineer the claim ceiling from the code. If
you are deciding whether to rely on an ICTS result, read this first.

Limitations are stated plainly here rather than distributed thinly through the documentation.

## 1. Only the first neutral property is implemented

Exactly one neutral property and one vector are implemented:
`CORE-PROP-EXT-EVIDENCE-001` / `ICTS-VEC-EXT-EVIDENCE-001`.

**Generalized five-vector v0 conformance is not established.** A result from this repository
speaks only to external-evidence acceptance. It says nothing about any other institutional
property.

## 2. H1 is established for one vector only

```
H1 PASS — EXT-EVIDENCE-001
```

H1 — harness independence — has been executed and passed. The frozen vector produced identical
normative terminal results across the bare-Python and Inspect AI reference implementations on
all 14 frozen cases. Independence is checked mechanically on every run: the Inspect harness
imports no bare-Python module and implements its own normalization, evidence-sufficiency, and
invariant-adjudication path. Evidence:
[`../reference/inspect_ai/H1_RESULT.json`](../reference/inspect_ai/H1_RESULT.json).

The bounded claim is **one vector, two implementations**. H1 does **not** establish full ICTS
harness independence, all properties, H2, field validity, field EPSR, vendor conformance, or
deployment certification.

What H1 does buy is narrow but real: it separates a property that belongs to the
**specification** from one that is an artifact of a single harness. A result that only one
implementation can reproduce is not a specification.

Note also that `ICTS_H1_INSPECT_v0.1.0` did not execute against its own Inspect pin, and that
this went unnoticed while the H1 CI job was advisory. The job is now a required-success gate.
See [`../reference/inspect_ai/CHANGELOG.md`](../reference/inspect_ai/CHANGELOG.md).

## 3. H2 is not established

Cross-boundary independence for a harder vector has not been attempted. It is not scheduled by
the current release.

## 4. Field EPSR is pending

```
FIELD_EPSR_PENDING
```

Field EPSR is defined in the vector over topology-eligible **deployments**, excluding
`NOT_APPLICABLE_TOPOLOGY`. No deployments have been measured, so there is no value.

The metric this repository does compute is `synthetic_case_adjudicability` (currently `k=6`,
`n=11`). **It is not an EPSR and must never be reported as one.** It is computed over synthetic
cases, and synthetic cases are not deployments.

## 5. Synthetic evidence is engineering evidence

Everything in `synthetic/` is engineering evidence: it shows the implementation behaves as
specified on cases the authors constructed.

It is **not** market validation, field validation, or evidence of usefulness. Passing 14
synthetic cases the authors wrote demonstrates internal consistency, not external validity.

No claim of field usefulness or live bank deployment is made or supported.

## 6. Topology declarations are controlled test inputs

Topology applicability is anchored to a frozen deployment topology declaration — deliberately,
so that missing telemetry cannot masquerade as structural non-applicability.

But in this release the topology declarations are **controlled test inputs written by the
authors**. Nothing yet corroborates a declared topology against the deployment it claims to
describe.

In the field, a topology declaration is an assertion by the party being tested. A deployment
that misdeclares itself as single-domain would obtain `NOT_APPLICABLE_TOPOLOGY` and escape the
property. Independent topology corroboration is an open problem, not a solved one.

## 7. `established_by_domain` proves declared identity only

The source-independence rule turns on `established_by_domain` in each condition result.

Under the current synthetic evidence model this proves **declared** identity. It is **not**
independently cryptographically established institutional identity.

Concretely: the suite verifies that the named establishing domain is not the originating
evidence domain, and that it is declared as independently administered in the frozen topology.
It does **not** verify that the named institution actually performed the establishment. A
cooperating adapter and evidence source could name a third domain untruthfully and the current
implementation would not detect it.

## 8. Stronger establishment requires a later evidence path

Closing limitation 7 requires an evidence path this release does not have: signed or
independently verifiable attestation, binding a condition result to the institution that
established it in a way the acting system cannot forge.

That is a specification and evidence-model change, and it belongs to a later version through
[`../governance/EXTERNAL_CHANGE_PROCESS.md`](../governance/EXTERNAL_CHANGE_PROCESS.md).

## 9. No result generalizes to a vendor or institution

**No claim that an entire vendor or institution globally "passes ICTS" follows from one
configuration-bound run.**

Every result applies to one deployment, one configuration, one frozen vector, and one admitted
evidence set. Change the configuration and the result no longer applies. There is no result in
the vocabulary that describes a vendor, a product, or an organization as a whole, and any
marketing claim of that shape is unsupported by this suite.

## 10. The blind independent review gate is not satisfied

Reviews of v0.1.0, v0.1.1, and v0.1.2 were conducted and drove real repairs, but none meets
the independence condition in
[`../governance/REVIEW_POLICY.md`](../governance/REVIEW_POLICY.md). Such reviews are labelled
`PRE-INDEPENDENCE_TECHNICAL_AUDIT`.

Obtaining one genuinely blind review of v0.1.2 remains an open gate.

## 11. The end-user CLI does not exist

`icts inspect`, `icts run`, and `icts report` describe the intended product interaction. They
are **not implemented**. Nothing in this repository provides them.

## 12. Provenance: the ZIP digest was not independently recomputed here

All 42 frozen manifest entries and the frozen manifest digest itself are verified
byte-for-byte on every CI run. The frozen **ZIP** digest was not recomputed in the environment
that populated this repository; it is declared and corroborated by the H1 package's manifest.
See [`../provenance/RELEASE_STATE.md`](../provenance/RELEASE_STATE.md).

## Summary

| Claim | Status |
| --- | --- |
| One neutral property executably specified | Established |
| Bare-Python reference implementation | Established |
| Provenance-constrained normalization load-bearing | Established |
| Mapper addition/subtraction attacks checked | Established |
| Topology identity anchored to frozen declaration | Established |
| Topology ineligibility distinct from observability failure | Established |
| Deterministic synthetic cases execute | Established |
| Adversarial regression passes locally | Established |
| Blind independent review gate | **Not established** |
| H1 harness independence, `EXT-EVIDENCE-001` | Established (one vector, two implementations) |
| Full ICTS harness independence, all properties | **Not established** |
| H2 | **Not established** |
| Field usefulness | **Not established** |
| Live bank deployment | **Not established** |
| Field EPSR | **Not established** (`FIELD_EPSR_PENDING`) |
| Cryptographic proof of `established_by_domain` | **Not established** |
| Generalized five-vector v0 conformance | **Not established** |
