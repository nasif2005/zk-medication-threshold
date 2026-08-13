#!/usr/bin/env python3
"""Collect reproducible witness, proving, and verification timings for Section 6.2.1."""

import argparse
import csv
import json
import platform
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def run_timed(command, cwd):
    started = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )
    return elapsed


def summary(values):
    return {
        "mean_s": statistics.mean(values),
        "stdev_s": statistics.stdev(values) if len(values) > 1 else 0.0,
        "median_s": statistics.median(values),
        "min_s": min(values),
        "max_s": max(values),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=30)
    parser.add_argument("--warmups", type=int, default=5)
    parser.add_argument("--node", default="node")
    parser.add_argument("--snarkjs", default="snarkjs")
    args = parser.parse_args()
    if args.runs < 1 or args.warmups < 0:
        parser.error("runs must be positive and warmups must be non-negative")

    script_dir = Path(__file__).resolve().parent
    eval_dir = script_dir.parent
    resource_dir = eval_dir.parent.parent
    result_dir = eval_dir / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    raw_path = result_dir / "raw_measurements.csv"
    summary_path = result_dir / "summary.csv"
    environment_path = result_dir / "environment.json"

    environment = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform.platform(),
        "python": sys.version,
        "node": shutil.which(args.node),
        "snarkjs": shutil.which(args.snarkjs),
        "runs": args.runs,
        "warmups": args.warmups,
    }
    environment_path.write_text(json.dumps(environment, indent=2) + "\n", encoding="utf-8")

    rows = []
    for k in (10, 15, 20):
        name = f"bounded_history_k{k}"
        build_dir = eval_dir / "build" / f"k{k}"
        input_path = eval_dir / "inputs" / f"k{k}_valid.json"
        wasm = build_dir / f"{name}_js" / f"{name}.wasm"
        witness_tool = build_dir / f"{name}_js" / "generate_witness.js"
        zkey = build_dir / f"{name}_final.zkey"
        vk = build_dir / f"{name}_vk.json"
        required = (input_path, wasm, witness_tool, zkey, vk)
        missing = [str(item) for item in required if not item.exists()]
        if missing:
            raise FileNotFoundError("Run build_variants.sh first. Missing:\n" + "\n".join(missing))

        def one_run(run_index, recorded):
            run_dir = result_dir / "artifacts" / f"k{k}" / f"run_{run_index:02d}"
            run_dir.mkdir(parents=True, exist_ok=True)
            witness = run_dir / "witness.wtns"
            proof = run_dir / "proof.json"
            public = run_dir / "public.json"
            witness_s = run_timed([args.node, str(witness_tool), str(wasm), str(input_path), str(witness)], resource_dir)
            prove_s = run_timed([args.snarkjs, "groth16", "prove", str(zkey), str(witness), str(proof), str(public)], resource_dir)
            verify_s = run_timed([args.snarkjs, "groth16", "verify", str(vk), str(public), str(proof)], resource_dir)
            if recorded:
                rows.append({"experiment": "bounded_history", "k": k, "depth": 2, "run": run_index,
                             "witness_s": witness_s, "prove_s": prove_s, "verify_s": verify_s,
                             "total_prover_s": witness_s + prove_s, "status": "success"})

        for warmup in range(1, args.warmups + 1):
            one_run(warmup, recorded=False)
        for run in range(1, args.runs + 1):
            one_run(run, recorded=True)

    fieldnames = ["experiment", "k", "depth", "run", "witness_s", "prove_s", "verify_s", "total_prover_s", "status"]
    with raw_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_rows = []
    for k in (10, 15, 20):
        subset = [row for row in rows if row["k"] == k]
        for metric in ("witness_s", "prove_s", "verify_s", "total_prover_s"):
            result = summary([row[metric] for row in subset])
            summary_rows.append({"experiment": "bounded_history", "k": k, "depth": 2, "metric": metric, **result})
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["experiment", "k", "depth", "metric", "mean_s", "stdev_s", "median_s", "min_s", "max_s"])
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"Wrote {raw_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
