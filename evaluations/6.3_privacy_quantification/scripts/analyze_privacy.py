#!/usr/bin/env python3
"""Derive architecture views and compute empirical ALI, MI, and expected ASP."""
import argparse, csv, json, math
from collections import Counter, defaultdict
from pathlib import Path

ARCHITECTURES=("centralized_plaintext","trusted_encrypted_database","zk_snark_hidden_state")
def entropy(values):
    c=Counter(values); n=len(values); return -sum((v/n)*math.log2(v/n) for v in c.values())
def mutual_information(xs,ys):
    joint=Counter(zip(xs,ys)); xc=Counter(xs); yc=Counter(ys); n=len(xs)
    return sum((v/n)*math.log2((v*n)/(xc[x]*yc[y])) for (x,y),v in joint.items())
def expected_asp(xs,ys):
    groups=defaultdict(Counter)
    for x,y in zip(xs,ys): groups[y][x]+=1
    return sum(max(c.values()) for c in groups.values())/len(xs)
def public_view(r): return (r["q_current"],r["t_current"],r["m_q"],r["window"],r["medication_id"],r["authorized"])
def history_view(r): return (r["history_prev_q"],r["history_prev_t"],*public_view(r))
def load_performance(path):
    if not path.exists(): return {}
    with path.open(newline="",encoding="utf-8") as f: return {r["metric"]:float(r["mean"]) for r in csv.DictReader(f)}
def validate(rows):
    fixed_fields=("q_current","t_current","m_q","window","medication_id")
    expected={field:rows[0][field] for field in fixed_fields}
    for row in rows:
        if any(row[field] != expected[field] for field in fixed_fields):
            raise ValueError("public request and policy inputs must be fixed across the primary workload")
        qs=json.loads(row["history_prev_q"]); ts=json.loads(row["history_prev_t"])
        if len(qs) != 10 or len(ts) != 10 or len(qs) != len(ts):
            raise ValueError(f"sample {row['sample_id']} does not contain a valid k=10 history")
        now=int(row["t_current"]); window=int(row["window"])
        x=sum(q for q,t in zip(qs,ts) if now-window < t <= now)
        if x != int(row["x_active_quantity"]):
            raise ValueError(f"sample {row['sample_id']} has an inconsistent X value")
        authorized=int(x+int(row["q_current"]) <= int(row["m_q"]))
        if authorized != int(row["authorized"]):
            raise ValueError(f"sample {row['sample_id']} has an inconsistent authorization outcome")
    if len({row["x_active_quantity"] for row in rows}) < 2:
        raise ValueError("at least two distinct X values are required")
    if {row["authorized"] for row in rows} != {"0","1"}:
        raise ValueError("both authorized and rejected observations are required")
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--workload",type=Path); ap.add_argument("--performance-summary",type=Path); ap.add_argument("--output-dir",type=Path); a=ap.parse_args()
    experiment=Path(__file__).resolve().parent.parent; package=experiment.parent.parent
    workload=a.workload or experiment/"workload"/"shared_histories.csv"; out=a.output_dir or experiment/"results"
    perf_path=a.performance_summary or package/"evaluations"/"6.2.3_privacy_overhead"/"results"/"summary.csv"
    with workload.open(newline="",encoding="utf-8") as f: rows=list(csv.DictReader(f))
    if not rows: raise ValueError("workload is empty")
    validate(rows)
    xs=[int(r["x_active_quantity"]) for r in rows]; prior=max(Counter(xs).values())/len(xs); hx=entropy(xs)
    views={"centralized_plaintext":[history_view(r) for r in rows],"trusted_encrypted_database":[history_view(r) for r in rows],"zk_snark_hidden_state":[public_view(r) for r in rows]}
    metrics=[]
    for arch in ARCHITECTURES:
        ys=views[arch]; asp=expected_asp(xs,ys)
        metrics.append({"architecture":arch,"ali_scalar_direct_disclosure":int(arch!="zk_snark_hidden_state"),"mutual_information_bits":mutual_information(xs,ys),"expected_asp":asp,"prior_asp":prior,"asp_advantage":asp-prior,"h_x_bits":hx,"samples":len(rows)})
    out.mkdir(parents=True,exist_ok=True)
    with (out/"privacy_metrics.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(metrics[0]));w.writeheader();w.writerows(metrics)
    observations=[]
    for r in rows:
        common={"sample_id":r["sample_id"],"x_active_quantity":r["x_active_quantity"],"authorized":r["authorized"]}
        observations += [{**common,"architecture":arch,"direct_x_visible":int(arch!="zk_snark_hidden_state"),"observable_y":json.dumps(views[arch][int(r["sample_id"])-1])} for arch in ARCHITECTURES]
    with (out/"architecture_observations.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(observations[0]));w.writeheader();w.writerows(observations)
    perf=load_performance(perf_path); latency={"centralized_plaintext":perf.get("plaintext_s"),"trusted_encrypted_database":None,"zk_snark_hidden_state":perf.get("zk_end_to_end_s")}
    trade=[{**m,"reported_mean_latency_s":"not_measured" if latency[m["architecture"]] is None else latency[m["architecture"]]} for m in metrics]
    with (out/"privacy_performance_tradeoff.csv").open("w",newline="",encoding="utf-8") as f: w=csv.DictWriter(f,fieldnames=list(trade[0]));w.writeheader();w.writerows(trade)
    summary={"workload":str(workload.resolve()),"performance_source":str(perf_path.resolve()),"x_min":min(xs),"x_max":max(xs),"x_distinct":len(set(xs)),"authorized":sum(int(r["authorized"]) for r in rows),"rejected":sum(1-int(r["authorized"]) for r in rows),"metrics":metrics,"notes":["ALI uses a scalar-level exact-disclosure unit for X.","The trusted encrypted-database adversary is inside the decryption boundary.","The zk view includes fixed public request/policy inputs and the authorization outcome.","Cryptographic encodings are excluded from categorical MI estimation.","Trusted encrypted-database latency was not measured in Section 6.2.3 and is not imputed."]}
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8"); print(f"Wrote privacy results to {out}")
if __name__ == "__main__": main()
