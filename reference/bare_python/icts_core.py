from __future__ import annotations
from typing import Any, Dict, List, Tuple

RESULTS = {"PASS", "FAIL", "NOT_TESTABLE", "NOT_APPLICABLE_TOPOLOGY", "INVALID_TEST_EXECUTION"}
PERMITTED_TRANSFORMS = {"DIRECT"}
REQUIRED_SINGLETON_TYPES = {"external_evidence", "acceptance_policy", "acceptance_evaluation", "action"}
DECISIONS = {"PERMIT", "DENY"}

class IntegrityError(Exception):
    pass

def _wrap(value: Any, obs_id: str, source_field: str) -> Dict[str, Any]:
    return {
        "value": value,
        "source_observation_id": obs_id,
        "source_field": source_field,
        "transform": "DIRECT",
    }

def _normalize_value(value: Any, obs_id: str, path: str) -> Any:
    if isinstance(value, dict):
        return {k: _normalize_value(v, obs_id, f"{path}.{k}" if path else k)
                for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize_value(v, obs_id, f"{path}[{i}]") for i, v in enumerate(value)]
    return _wrap(value, obs_id, path)

def normalize(native: Dict[str, Any]) -> Dict[str, Any]:
    out = {"fixture_id": native.get("fixture_id"), "observations": []}
    for event in native.get("events", []):
        obs_id = event.get("event_id")
        typ = event.get("type")
        if not isinstance(obs_id, str) or not obs_id:
            raise IntegrityError("native event missing valid event_id")
        if not isinstance(typ, str) or not typ:
            raise IntegrityError(f"native event {obs_id} missing valid type")
        fields = {}
        for key, value in event.items():
            if key in ("event_id", "type"):
                continue
            fields[key] = _normalize_value(value, obs_id, key)
        out["observations"].append({
            "event_id": _wrap(obs_id, obs_id, "event_id"),
            "type": _wrap(typ, obs_id, "type"),
            "fields": fields,
        })
    return out

def _native_by_id(native: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    idx = {}
    for e in native.get("events", []):
        eid = e.get("event_id")
        if not isinstance(eid, str) or not eid:
            raise IntegrityError("native event missing valid event_id")
        if eid in idx:
            raise IntegrityError(f"duplicate native event_id: {eid}")
        idx[eid] = e
    return idx

def _resolve_source(native_event: Dict[str, Any], source_field: str) -> Any:
    if source_field in ("event_id", "type"):
        return native_event.get(source_field)

    cur: Any = native_event
    token = ""
    i = 0
    parts = []
    while i < len(source_field):
        c = source_field[i]
        if c == ".":
            if token:
                parts.append(("key", token)); token = ""
            i += 1
        elif c == "[":
            if token:
                parts.append(("key", token)); token = ""
            j = source_field.find("]", i)
            if j < 0:
                raise IntegrityError(f"malformed source_field: {source_field}")
            parts.append(("index", int(source_field[i+1:j])))
            i = j + 1
        else:
            token += c
            i += 1
    if token:
        parts.append(("key", token))

    for kind, val in parts:
        if kind == "key":
            if not isinstance(cur, dict) or val not in cur:
                raise IntegrityError(f"source_field does not resolve: {source_field}")
            cur = cur[val]
        else:
            if not isinstance(cur, list) or val < 0 or val >= len(cur):
                raise IntegrityError(f"source_field index does not resolve: {source_field}")
            cur = cur[val]
    return cur

def _validate_leaf(w: Any, native_idx: Dict[str, Dict[str, Any]], expected_path: str) -> None:
    if not isinstance(w, dict):
        raise IntegrityError(f"normative leaf at {expected_path} is not provenance-wrapped")
    required = {"value", "source_observation_id", "source_field", "transform"}
    if not required.issubset(w):
        raise IntegrityError(f"normative leaf at {expected_path} missing provenance metadata")
    if w["transform"] not in PERMITTED_TRANSFORMS:
        raise IntegrityError(f"forbidden normative transform at {expected_path}: {w['transform']}")
    sid = w["source_observation_id"]
    sf = w["source_field"]
    if sid not in native_idx:
        raise IntegrityError(f"unresolvable source_observation_id at {expected_path}: {sid}")
    if sf != expected_path:
        raise IntegrityError(f"DIRECT source_field mismatch at {expected_path}: {sf}")
    src_val = _resolve_source(native_idx[sid], sf)
    if w["value"] != src_val:
        raise IntegrityError(f"normalized value differs from native source at {expected_path}")

def _validate_tree(x: Any, native_idx: Dict[str, Dict[str, Any]], path: str) -> None:
    if isinstance(x, dict) and {"value", "source_observation_id", "source_field", "transform"}.issubset(x):
        _validate_leaf(x, native_idx, path)
        return
    if isinstance(x, dict):
        for k, v in x.items():
            _validate_tree(v, native_idx, f"{path}.{k}" if path else k)
        return
    if isinstance(x, list):
        for i, v in enumerate(x):
            _validate_tree(v, native_idx, f"{path}[{i}]")
        return
    raise IntegrityError(f"unwrapped normative value at {path}")

def _native_field_paths(value: Any, path: str, acc: set) -> None:
    if isinstance(value, dict):
        for k, v in value.items():
            _native_field_paths(v, f"{path}.{k}" if path else k, acc)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            _native_field_paths(v, f"{path}[{i}]", acc)
    else:
        acc.add(path)

def _normalized_field_paths(x: Any, path: str, acc: set) -> None:
    if isinstance(x, dict) and {"value", "source_observation_id", "source_field", "transform"}.issubset(x):
        acc.add(path)
        return
    if isinstance(x, dict):
        for k, v in x.items():
            _normalized_field_paths(v, f"{path}.{k}" if path else k, acc)
        return
    if isinstance(x, list):
        for i, v in enumerate(x):
            _normalized_field_paths(v, f"{path}[{i}]", acc)

def validate_normalized(normalized: Dict[str, Any], native: Dict[str, Any]) -> None:
    native_idx = _native_by_id(native)
    observations = normalized.get("observations")
    if not isinstance(observations, list):
        raise IntegrityError("normalized observations missing or not a list")
    if len(observations) != len(native_idx):
        raise IntegrityError(
            f"normalized observation count {len(observations)} != native event count {len(native_idx)}"
        )

    seen_ids = set()
    for obs in observations:
        if not isinstance(obs, dict):
            raise IntegrityError("normalized observation is not an object")
        event_id_w = obs.get("event_id")
        type_w = obs.get("type")
        if not isinstance(event_id_w, dict) or "value" not in event_id_w:
            raise IntegrityError("normalized event_id missing")
        eid = event_id_w["value"]
        if eid in seen_ids:
            raise IntegrityError(f"duplicate normalized event_id: {eid}")
        seen_ids.add(eid)
        _validate_leaf(event_id_w, native_idx, "event_id")
        _validate_leaf(type_w, native_idx, "type")
        fields = obs.get("fields")
        if not isinstance(fields, dict):
            raise IntegrityError(f"normalized fields missing for event {eid}")
        for key, value in fields.items():
            if key == "derived_diagnostic":
                continue
            _validate_tree(value, native_idx, key)

        # Completeness is normative: a mapper may not silently subtract native
        # evidence fields from the normalized set used by downstream predicates.
        expected_paths: set = set()
        for k, v in native_idx[eid].items():
            if k in ("event_id", "type"):
                continue
            _native_field_paths(v, k, expected_paths)
        observed_paths: set = set()
        for k, v in fields.items():
            if k == "derived_diagnostic":
                continue
            _normalized_field_paths(v, k, observed_paths)
        missing = expected_paths - observed_paths
        if missing:
            raise IntegrityError(
                f"normalization omitted native field(s) for event {eid}: {sorted(missing)[:5]}"
            )

def _unwrap(w: Any) -> Any:
    if not isinstance(w, dict) or "value" not in w:
        raise IntegrityError("attempt to read non-wrapped normative leaf")
    return w["value"]

def _event_id(obs: Dict[str, Any]) -> str:
    return _unwrap(obs["event_id"])

def _event_type(obs: Dict[str, Any]) -> str:
    return _unwrap(obs["type"])

def _index_events(normalized: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    idx: Dict[str, Dict[str, Any]] = {}
    counts: Dict[str, int] = {}
    for obs in normalized["observations"]:
        typ = _event_type(obs)
        counts[typ] = counts.get(typ, 0) + 1
        if typ in REQUIRED_SINGLETON_TYPES and counts[typ] > 1:
            raise IntegrityError(f"duplicate normative singleton event type: {typ}")
        if typ not in idx:
            idx[typ] = obs
    return idx

def _field(obs: Dict[str, Any], *path: Any) -> Any:
    cur: Any = obs["fields"]
    for p in path:
        if isinstance(p, int):
            if not isinstance(cur, list) or p >= len(cur):
                raise KeyError(path)
            cur = cur[p]
        else:
            if not isinstance(cur, dict) or p not in cur:
                raise KeyError(path)
            cur = cur[p]
    return _unwrap(cur)

def _field_or_none(obs: Dict[str, Any], *path: Any) -> Any:
    try:
        return _field(obs, *path)
    except KeyError:
        return None

def validate_topology(topology: Dict[str, Any]) -> None:
    if not isinstance(topology.get("deployment_id"), str) or not topology["deployment_id"]:
        raise IntegrityError("topology missing deployment_id")
    domains = topology.get("domains")
    rel = topology.get("relationship")
    if not isinstance(domains, list) or not domains:
        raise IntegrityError("topology domains missing")
    if not isinstance(rel, dict):
        raise IntegrityError("topology relationship missing")
    ids = []
    for d in domains:
        if not isinstance(d, dict) or not isinstance(d.get("domain_id"), str):
            raise IntegrityError("malformed topology domain")
        ids.append(d["domain_id"])
    if len(ids) != len(set(ids)):
        raise IntegrityError("duplicate topology domain_id")
    if not isinstance(rel.get("cross_domain"), bool):
        raise IntegrityError("topology cross_domain must be boolean")
    if not isinstance(rel.get("external_evidence_relationship"), bool):
        raise IntegrityError("topology external_evidence_relationship must be boolean")
    acting = rel.get("acting_system")
    if acting not in ids:
        raise IntegrityError("topology acting_system not declared")

def topology_applicable(topology: Dict[str, Any]) -> bool:
    validate_topology(topology)
    ids = [d["domain_id"] for d in topology["domains"]]
    rel = topology["relationship"]
    origin = rel.get("evidence_origin")
    if len(ids) < 2:
        return False
    if not rel["cross_domain"] or not rel["external_evidence_relationship"]:
        return False
    if origin not in ids or origin == rel["acting_system"]:
        return False
    return True


def validate_topology_bindings(normalized: Dict[str, Any], topology: Dict[str, Any]) -> None:
    """Bind stream-supplied domain identifiers to the frozen topology declaration."""
    ev = _index_events(normalized)
    rel = topology["relationship"]

    ext = ev.get("external_evidence")
    if ext is not None:
        source_domain = _field_or_none(ext, "source_domain")
        if source_domain is not None and source_domain != rel.get("evidence_origin"):
            raise IntegrityError(
                f"external_evidence.source_domain {source_domain!r} does not match "
                f"declared topology evidence_origin {rel.get('evidence_origin')!r}"
            )

    pol = ev.get("acceptance_policy")
    if pol is not None:
        acting_domain = _field_or_none(pol, "acting_domain")
        if acting_domain is not None and acting_domain != rel.get("acting_system"):
            raise IntegrityError(
                f"acceptance_policy.acting_domain {acting_domain!r} does not match "
                f"declared topology acting_system {rel.get('acting_system')!r}"
            )

def evidence_sufficient(normalized: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    ev = _index_events(normalized)
    ext = ev.get("external_evidence")
    pol = ev.get("acceptance_policy")
    ae = ev.get("acceptance_evaluation")
    act = ev.get("action")

    if not ext: reasons.append("missing external_evidence")
    if not pol: reasons.append("missing acceptance_policy")
    if not ae: reasons.append("missing acceptance_evaluation")
    if not act: reasons.append("missing action")
    if reasons:
        return False, reasons

    evidence_id = _field_or_none(ext, "evidence_id")
    source_domain = _field_or_none(ext, "source_domain")
    target_domain = _field_or_none(ext, "target_domain")
    if not evidence_id: reasons.append("external_evidence.evidence_id absent")
    if not source_domain: reasons.append("external_evidence.source_domain absent")
    if not target_domain: reasons.append("external_evidence.target_domain absent")

    policy_id = _field_or_none(pol, "policy_id")
    acting_domain = _field_or_none(pol, "acting_domain")
    if not policy_id: reasons.append("acceptance_policy.policy_id absent")
    if acting_domain != target_domain:
        reasons.append("acceptance_policy.acting_domain != external_evidence.target_domain")

    required_wrapped = pol["fields"].get("required_conditions")
    required = None
    if isinstance(required_wrapped, list):
        try:
            required = [_unwrap(x) for x in required_wrapped]
        except IntegrityError:
            raise
    if not isinstance(required, list) or not required:
        reasons.append("acceptance_policy.required_conditions absent/empty")

    if _field_or_none(ae, "evidence_id") != evidence_id:
        reasons.append("acceptance_evaluation.evidence_id mismatch")

    cr = ae["fields"].get("condition_results")
    if not isinstance(cr, dict):
        reasons.append("acceptance_evaluation.condition_results absent")
    elif isinstance(required, list):
        for cond in required:
            if cond not in cr or not isinstance(cr[cond], dict):
                reasons.append(f"condition result missing: {cond}")
                continue
            value = _field_or_none(ae, "condition_results", cond, "value")
            estab = _field_or_none(ae, "condition_results", cond, "established_by_domain")
            if not isinstance(value, bool):
                reasons.append(f"condition value missing/non-boolean: {cond}")
            if not isinstance(estab, str) or not estab:
                reasons.append(f"established_by_domain missing: {cond}")

    if _field_or_none(act, "used_evidence_id") != evidence_id:
        reasons.append("action.used_evidence_id mismatch")
    if _field_or_none(act, "parent_event_id") != _event_id(ae):
        reasons.append("action.parent_event_id not causally linked to acceptance_evaluation")

    decision = _field_or_none(act, "decision")
    if decision not in DECISIONS:
        reasons.append("action.decision missing or unsupported")

    return len(reasons) == 0, reasons

def invariant_holds(normalized: Dict[str, Any], topology: Dict[str, Any]) -> Tuple[bool, List[str]]:
    ev = _index_events(normalized)
    ext, pol, ae, act = ev["external_evidence"], ev["acceptance_policy"], ev["acceptance_evaluation"], ev["action"]
    decision = _field(act, "decision")
    if decision == "DENY":
        return True, ["observed action was denied; external evidence did not authorize the action"]

    source_domain = _field(ext, "source_domain")
    acting_domain = _field(pol, "acting_domain")
    declared_domains = {d["domain_id"] for d in topology["domains"]}
    rel = topology["relationship"]

    # Identity used by the invariant is anchored to the frozen topology, not
    # accepted from self-naming fields in the observation stream.
    if source_domain != rel.get("evidence_origin"):
        raise IntegrityError(
            f"external_evidence.source_domain {source_domain!r} does not match "
            f"declared topology evidence_origin {rel.get('evidence_origin')!r}"
        )
    if acting_domain != rel.get("acting_system"):
        raise IntegrityError(
            f"acceptance_policy.acting_domain {acting_domain!r} does not match "
            f"declared topology acting_system {rel.get('acting_system')!r}"
        )

    required = [_unwrap(x) for x in pol["fields"]["required_conditions"]]
    violations: List[str] = []

    for cond in required:
        value = _field(ae, "condition_results", cond, "value")
        estab = _field(ae, "condition_results", cond, "established_by_domain")
        if value is not True:
            violations.append(f"required condition unsatisfied: {cond}")
        if estab == source_domain:
            violations.append(f"originating source self-established admissibility condition: {cond}")
        elif estab not in declared_domains:
            violations.append(f"condition established by undeclared domain: {cond}")

    return len(violations) == 0, violations

def adjudicate(native: Dict[str, Any], topology: Dict[str, Any], normalizer=normalize) -> Dict[str, Any]:
    try:
        validate_topology(topology)
        if not topology_applicable(topology):
            return {
                "result": "NOT_APPLICABLE_TOPOLOGY",
                "evidence_path": None,
                "details": ["frozen deployment topology cannot instantiate cross-domain external-evidence reliance"],
            }

        normalized = normalizer(native)
        validate_normalized(normalized, native)
        validate_topology_bindings(normalized, topology)

        sufficient, suff_reasons = evidence_sufficient(normalized)
        if not sufficient:
            return {
                "result": "NOT_TESTABLE",
                "evidence_path": None,
                "details": suff_reasons,
                "normalized_observation_count": len(normalized["observations"]),
            }

        holds, violations = invariant_holds(normalized, topology)
        return {
            "result": "PASS" if holds else "FAIL",
            "evidence_path": "EA-1",
            "details": violations,
            "normalized_observation_count": len(normalized["observations"]),
        }
    except IntegrityError as e:
        return {"result": "INVALID_TEST_EXECUTION", "evidence_path": None, "details": [str(e)]}
    except Exception as e:
        return {"result": "INVALID_TEST_EXECUTION", "evidence_path": None, "details": [f"{type(e).__name__}: {e}"]}
