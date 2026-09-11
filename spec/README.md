# Specification

This directory is the normative part of ICTS. It is what a third party implements.

Everything under `reference/` is replaceable. This directory is not.

## The normative / non-normative boundary

| Directory | Status | Role |
| --- | --- | --- |
| `spec/core/` | **Normative** | Architecture-neutral institutional properties |
| `spec/icts/` | **Normative** | ICTS deployment-test semantics |
| `synthetic/` | **Normative inputs** | Frozen fixtures, topologies, and oracles |
| `reference/` | Non-normative | Replaceable implementations |

**Reference implementation behavior must not become the specification by accident.** If the
reference implementation and this directory disagree, that is a defect. The resolution is to
state the intended semantics here, not to retrofit a description of what the code happens to
do.

A third party must be able to implement this specification independently, without reading
`reference/`. If that is not possible for some part of the specification, that gap is itself
a reportable defect.

## `spec/core/` — architecture-neutral properties

`spec/core/` contains institutional properties stated without reference to any particular
architecture. A core property must not depend on:

- Authority VM;
- OIC;
- VEIP;
- ZTL;
- Veraxis product terminology;
- one particular model vendor;
- one policy engine;
- one observability vendor.

A property that cannot be stated without one of those is not a core property.

Current contents:

- [`core/CORE-PROP-EXT-EVIDENCE-001.md`](core/CORE-PROP-EXT-EVIDENCE-001.md) — External
  Evidence Acceptance. The first and currently only neutral property.

## `spec/icts/` — deployment-test semantics

`spec/icts/` says how a core property becomes an executable deployment test.

- [`icts/ICTS-VEC-EXT-EVIDENCE-001.json`](icts/ICTS-VEC-EXT-EVIDENCE-001.json) — the
  **vector**. Binds the property to required singleton event types, the topology
  requirement, topology binding rules, duplicate-event semantics, the result vocabulary, and
  the field EPSR definition (`FIELD_EPSR_PENDING`).
- [`icts/ESC-EXT-EVIDENCE-001.json`](icts/ESC-EXT-EVIDENCE-001.json) — the **Evidence
  Sufficiency Contract**. Determines whether admitted observations are sufficient to
  adjudicate. It does **not** determine whether the property passes.
- [`icts/NPC-EXT-EVIDENCE-001.json`](icts/NPC-EXT-EVIDENCE-001.json) — the **Normalization
  Provenance Contract**. Constrains what normalization may do to normative values.
- [`icts/RESULT_VOCABULARY.md`](icts/RESULT_VOCABULARY.md) — the five terminal results.

## The two-predicate rule

> Evidence sufficiency establishes adjudicability, not conformance.

These are two separate predicates and they are specified in two separate artifacts on
purpose:

1. The **Evidence Sufficiency Contract** asks: can this be adjudicated at all?
2. The **invariant predicate** asks: did the property hold?

Collapsing them is the most common way a conformance suite becomes meaningless. A suite that
returns `FAIL` when it simply could not see enough has not tested anything; it has punished
observability gaps. ICTS returns `NOT_TESTABLE` there instead.

## Source independence

> The source of evidence must not be allowed to define the conditions under which that
> evidence counts.

This is enforced mechanically, not by convention. An acceptance condition established by the
originating evidence domain does not count. An independently administered third declared
domain may establish a condition; the originating source may not.

## Stability

Every file in this directory is pinned in `MANIFEST.json` and verified on every CI run.
Changing one is a versioned event, never a patch. See
[`../governance/EXTERNAL_CHANGE_PROCESS.md`](../governance/EXTERNAL_CHANGE_PROCESS.md).
