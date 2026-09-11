# Inspect AI second harness (H1)

> ## `H1 PASS — EXT-EVIDENCE-001`
>
> The frozen vector produced **identical normative terminal results** across the
> bare-Python and Inspect AI reference implementations: **14/14 frozen cases**.
>
> Evidence: [`H1_RESULT.json`](H1_RESULT.json) ·
> [`H1_INDEPENDENCE_RECORD.json`](H1_INDEPENDENCE_RECORD.json)
> `normative_comparison_sha256 = cf1a536def94b6ecc5ef1f9c4ee69eae5c1815918a207f73365977ad2d690643`

Current version: **`ICTS_H1_INSPECT_v0.1.1`** · pinned to `inspect-ai==0.3.263`.
See [`CHANGELOG.md`](CHANGELOG.md).

## What H1 establishes

H1 is the **harness independence** gate. It asks one narrow question:

> Does the same frozen vector produce identical normative terminal results in two
> independent harness implementations?

The bounded claim now supported:

> **H1 established for `ICTS-VEC-EXT-EVIDENCE-001`:** the frozen vector produced
> identical normative terminal results across the bare-Python and Inspect AI
> reference implementations.

That is one vector, two implementations. It is what separates a property that
belongs to the **specification** from one that is an artifact of a single
harness.

## What H1 does not establish

H1 does **not** establish:

- full ICTS harness independence;
- all properties;
- H2 (cross-boundary independence for a harder vector);
- field usefulness or field validity;
- field EPSR — still `FIELD_EPSR_PENDING`;
- vendor conformance;
- deployment certification;
- the blind independent review gate, which remains **owed**.

## Independence boundary

H1 is meaningless if the second harness calls the first. Independence is checked
**mechanically on every run**, not asserted:

| Check | Method | Result |
| --- | --- | --- |
| No bare-Python import | Static AST of `inspect_harness.py` | imports only `__future__`, `json`, `typing`, `inspect_ai*` |
| No indirect route | Textual scan for `icts_core` / `bare_python` | none found |
| No runtime leak | `sys.modules` after import | no bare-Python module loaded |
| Own normative path | Module ownership of `normalize`, `evidence_sufficient`, `invariant_holds`, `adjudicate` | all resolve to `inspect_harness` |

Both harnesses consume the same frozen normative **inputs** — property, ESC, NPC,
topology declarations, fixtures, case set — which is exactly what H1 requires.
They implement the normative evaluation path independently.

`run_h1.py` runs the bare-Python suite as a separate **subprocess** to obtain the
comparison baseline. The Inspect harness itself never imports or invokes it.

## Files

| File | Role |
| --- | --- |
| `inspect_harness.py` | Independent implementation as an Inspect task, solver, and scorer |
| `run_h1.py` | Runs both harnesses over the frozen vector and compares case by case |
| `H1_RESULT.json` | Committed gate evidence |
| `H1_INDEPENDENCE_RECORD.json` | Committed independence record |
| `INSPECT_PIN.json` | Exact pin with wheel and source digests |
| `requirements.txt` | `inspect-ai==0.3.263` |
| `CHANGELOG.md` | H1 harness changelog, including the v0.1.0 defect |

## Running

```bash
python -m pip install -r reference/inspect_ai/requirements.txt
python reference/inspect_ai/run_h1.py --frozen-tree .
```

Exactly one input mode is required, and no directory is ever searched implicitly:

| Mode | Behavior |
| --- | --- |
| `--frozen-tree REPO_ROOT` | Runs the v0.1.2 integrity gate (all 42 manifest entries verified byte-for-byte), then reconstitutes the exact frozen package |
| `--frozen-zip ZIP` | Verifies the archive SHA-256 against the frozen digest before extraction |

Both then verify the frozen manifest digest, so they converge on the same frozen
normative inputs. Neither mode weakens frozen-package verification.

### Terminal states

| Terminal | Exit | Meaning |
| --- | --- | --- |
| `H1_PASS` | 0 | Every frozen case: `bare == inspect == expected` |
| `H1_FAIL` | 1 | Any case differs |
| `H1_NOT_EXECUTED` | 2 | Environment or runtime prevented execution |

An execution failure is never converted into a pass. `H1_NOT_EXECUTED` is
deliberately distinct from `H1_FAIL`: "the gate could not run" and "the gate ran
and the harnesses disagreed" are different facts.

## Evidence

`H1_RESULT.json` records every case individually —
`case_id / expected / bare_python_result / inspect_ai_result / equivalent`. No
aggregate-only comparison is used anywhere in the gate.

Its **normative portion** (gate, versions, vector, property, frozen manifest
digest, comparisons, terminal) contains no timestamps and nothing
environment-specific, and is digested as `normative_comparison_sha256`. Run
metadata is kept separate. The file as a whole is **not** byte-reproducible
across environments and is not claimed to be; the normative portion and its
digest are, and CI checks the committed evidence against a fresh run.

## CI

H1 is a **required-success** job on Python 3.11 and 3.12. It is no longer
`continue-on-error`.

The bare-Python core keeps its broader 3.9–3.12 matrix. H1 is not forced onto a
Python version unsupported by the Inspect dependency chain merely to match it.

This matters: in v0.1.0 the H1 job was advisory, so a harness that could not even
import produced no failing signal, and the defect reached the public repository.
