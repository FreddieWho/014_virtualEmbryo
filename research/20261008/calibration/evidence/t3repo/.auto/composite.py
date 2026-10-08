#!/usr/bin/env python3
"""Compute the frozen 8-channel composite from a scorer JSON (or a metrics dict).

Usage:
  python .auto/composite.py <score.json>              -> prints COMPOSITE + channel table
  python .auto/composite.py --metrics '<json dict>'   -> same, from an inline metrics dict

Baseline composite is 0.0 by construction (all gains 0).
See .auto/composite_config.json for the frozen definition (directions verified from source).
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

CFG = Path(__file__).resolve().parent / "composite_config.json"


def load_cfg() -> dict:
    return json.loads(CFG.read_text())


def channel_value(metrics: dict, m: str):
    if m == "abs(scale_log_ratio)":
        v = metrics.get("scale_log_ratio")
        return abs(float(v)) if isinstance(v, (int, float)) else None
    v = metrics.get(m)
    return float(v) if isinstance(v, (int, float)) else None


def composite(metrics: dict, cfg: dict | None = None) -> dict:
    cfg = cfg or load_cfg()
    W = float(cfg["winsor"])
    gains, worst = {}, None
    for ch in cfg["channels"]:
        name, m, b, d = ch["channel"], ch["metric"], float(ch["baseline"]), int(ch["dir"])
        v = channel_value(metrics, m)
        if v is None or b == 0:
            gains[name] = None
            continue
        g = d * (v - b) / b
        g = max(-W, min(W, g))
        gains[name] = g
        if worst is None or g < gains[worst]:
            worst = name
    valid = [g for g in gains.values() if g is not None]
    comp = 100.0 * sum(valid) / len(valid) if valid else None
    guard = {}
    gr = cfg["guardrails"]
    de = metrics.get("de_score")
    lsr = metrics.get("library_size_ratio")
    vr = metrics.get("variance_ratio")
    pbe = metrics.get("pb_rel_err")
    if isinstance(de, (int, float)):
        guard["de_score_min"] = bool(de >= gr["de_score_min"])
    if isinstance(lsr, (int, float)):
        guard["library_size_ratio_max"] = bool(lsr <= gr["library_size_ratio_max"])
    if isinstance(vr, (int, float)):
        lo, hi = gr["variance_ratio_range"]
        guard["variance_ratio_range"] = bool(lo <= vr <= hi)
    if isinstance(pbe, (int, float)):
        guard["pb_rel_err_max"] = bool(pbe <= gr["pb_rel_err_max"])
    expr = [gains[k] for k in ("de", "dir", "mmd_u", "vario", "nmmd") if gains.get(k) is not None]
    expr_comp = 100.0 * sum(expr) / len(expr) if expr else None
    return {"composite": comp, "expr_composite": expr_comp, "gains": gains, "worst_channel": worst,
            "guardrails": guard, "guardrails_pass": all(guard.values()) if guard else None}


def main() -> int:
    if len(sys.argv) >= 3 and sys.argv[1] == "--metrics":
        metrics = json.loads(sys.argv[2])
    else:
        payload = json.loads(Path(sys.argv[1]).read_text())
        metrics = payload.get("metrics", payload)
    r = composite(metrics)
    for ch, g in r["gains"].items():
        n = metrics.get("scale_log_ratio") if ch == "scale" else None
        print(f"GAIN {ch}={g if g is None else round(g, 5)}")
    print(f"COMPOSITE={r['composite'] if r['composite'] is None else round(r['composite'], 4)}")
    print(f"EXPR_COMPOSITE={r['expr_composite'] if r['expr_composite'] is None else round(r['expr_composite'], 4)}")
    print(f"WORST_CHANNEL={r['worst_channel']}")
    print(f"GUARDRAILS_PASS={r['guardrails_pass']}")
    for k, v in r["guardrails"].items():
        print(f"GUARD {k}={v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
