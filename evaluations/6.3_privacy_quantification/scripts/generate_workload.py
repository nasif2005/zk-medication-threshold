#!/usr/bin/env python3
"""Generate one reproducible history population for all privacy architectures."""
import argparse, csv, json, random
from pathlib import Path

DEFAULTS = {"k": 10, "q_current": 10, "t_current": 100, "m_q": 60, "window": 30, "medication_id": 42}

def active_sum(qs, ts, now, window):
    return sum(q for q, t in zip(qs, ts) if now - window < t <= now)

def generate_history(rng, k, now, window):
    active_n = rng.randint(0, min(5, k - 1))
    expired_n = rng.randint(0, min(3, k - active_n - 1))
    entries = [(rng.randint(1, 20), rng.randint(now-window+1, now)) for _ in range(active_n)]
    entries += [(rng.randint(1, 20), rng.randint(1, now-window)) for _ in range(expired_n)]
    rng.shuffle(entries)
    entries += [(0, 0)] * (k - len(entries))
    return [q for q, _ in entries], [t for _, t in entries]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--samples", type=int, default=10000); ap.add_argument("--seed", type=int, default=20260813); ap.add_argument("--output", type=Path); a = ap.parse_args()
    if a.samples < 2: raise ValueError("--samples must be at least 2")
    experiment = Path(__file__).resolve().parent.parent
    output = a.output or experiment / "workload" / "shared_histories.csv"
    output.parent.mkdir(parents=True, exist_ok=True); rng = random.Random(a.seed); rows = []
    for sample_id in range(1, a.samples + 1):
        q, t = generate_history(rng, DEFAULTS["k"], DEFAULTS["t_current"], DEFAULTS["window"])
        x = active_sum(q, t, DEFAULTS["t_current"], DEFAULTS["window"])
        rows.append({"sample_id": sample_id, "history_prev_q": json.dumps(q,separators=(",",":")), "history_prev_t": json.dumps(t,separators=(",",":")), "x_active_quantity": x, "q_current": DEFAULTS["q_current"], "t_current": DEFAULTS["t_current"], "m_q": DEFAULTS["m_q"], "window": DEFAULTS["window"], "medication_id": DEFAULTS["medication_id"], "authorized": int(x + DEFAULTS["q_current"] <= DEFAULTS["m_q"])})
    with output.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    metadata={"seed":a.seed,"samples":a.samples,"parameters":DEFAULTS,"sensitive_variable":"sum(q_i * 1[t_current-window < t_i <= t_current])","workload":str(output.resolve())}
    (output.parent/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n",encoding="utf-8")
    print(f"Wrote {len(rows)} shared histories to {output}")
if __name__ == "__main__": main()
