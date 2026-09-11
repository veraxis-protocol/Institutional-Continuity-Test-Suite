# Inspect AI second harness (H1)

> ## `H1 NOT ESTABLISHED`
> ## `H1 EXECUTION PENDING`

This directory contains the `ICTS_H1_INSPECT_v0.1.0` package, carried byte-for-byte. It is
**work in progress**. Nothing in this repository claims H1 is passed.

## What H1 is

H1 is the **harness independence** gate. It asks one narrow question:

> Does the same frozen vector produce equivalent normative terminal results in two
> independent harness implementations?

If and when H1 is executed and passes, that is *all* it establishes. H1 does **not**
establish:

- H2 cross-boundary independence for a harder vector;
- field usefulness;
- field EPSR;
- topology corroboration in a live deployment;
- the blind independent review gate for v0.1.2;
- all-suite conformance.

## Independence boundary

`inspect_harness.py` does **not** import `reference/bare_python/icts_core.py`. It
independently implements the same frozen property, NPC/ESC semantics, topology binding, result
vocabulary, and case set through Inspect's Task/Solver/Scorer path, with its own `normalize`
and `adjudicate`.

That structural independence has been confirmed by inspection. It is a precondition for H1
meaning anything: a second harness that called into the first would prove nothing.

## Files

| File | Role |
| --- | --- |
| `inspect_harness.py` | Independent implementation as an Inspect task, solver, and scorer |
| `run_h1.py` | Runs both harnesses over the frozen vector and compares terminal results |
| `INSPECT_PIN.json` | Exact pin with wheel and source digests |
| `requirements.txt` | `inspect-ai==0.3.263` |

## Pin

```
inspect-ai==0.3.263
```

PyPI release date 2026-09-04. Wheel and source SHA-256 digests are in `INSPECT_PIN.json`.

## Running

```bash
python -m pip install -r reference/inspect_ai/requirements.txt
python reference/inspect_ai/run_h1.py
```

Expected terminal on success: `H1_PASS`, plus an `H1_RESULT.json` in this directory.

### Two things currently block that command

**1. `run_h1.py` requires the frozen ZIP.**

`run_h1.py` expects `ICTS_v0_C18_SYNTHETIC_FIRST_v0.1.2.zip` beside it and verifies its
SHA-256 against
`a3f225bd493f297d340688345a686f16cd16df14cf39676621e1d6232b2d070b` before doing anything.
That archive is **not committed here** — this repository carries the extracted, individually
hash-verified tree instead. To run H1 as written, place the frozen ZIP in this directory.

**2. The harness does not currently load under its own pin.**

`inspect_harness.py` declares its scorer with a bare decorator:

```python
@scorer
def icts_c18_scorer():
```

Under the pinned `inspect-ai==0.3.263`, `@scorer` requires a `metrics` argument, so importing
the task raises:

```
TypeError: scorer.<locals>.wrapper() missing 1 required positional argument: 'scorer_type'
```

This is a defect in `ICTS_H1_INSPECT_v0.1.0`, not in the frozen v0.1.2 candidate. It is
recorded here rather than silently patched, because the H1 package is a candidate under
development and quietly editing a candidate is exactly what
[`../../review/BLIND_REVIEW_PROTOCOL.md`](../../review/BLIND_REVIEW_PROTOCOL.md) forbids.
Fixing it is a versioned change to the H1 package through
[`../../governance/EXTERNAL_CHANGE_PROCESS.md`](../../governance/EXTERNAL_CHANGE_PROCESS.md).

## Why H1 is still not established

A diagnostic run has been performed against the byte-exact frozen v0.1.2 tree with a local
one-line decorator correction applied **outside** this repository. In that run, all 14 cases
produced equivalent terminal results across both harnesses.

That is a useful signal about where the work stands. It is **not** the H1 gate, for three
reasons:

1. the harness was locally modified to run at all;
2. the run bypassed `run_h1.py`'s ZIP-digest gate;
3. the corrected harness is not what is committed here.

H1 is established only when the committed, unmodified H1 package executes under its own pin
and produces equivalent normative terminal results against the frozen vector. Until then this
directory reads `H1 EXECUTION PENDING`, and no claim of harness independence should be made.

## CI

H1 is deliberately **not** part of the core conformance gate. An unavailable or broken
optional harness must never make the core suite unusable, so
`.github/workflows/test.yml` runs it as a separate, non-blocking job.
