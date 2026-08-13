#!/usr/bin/env bash
set -euo pipefail

# Run from the paper5 resource directory.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
EVAL_DIR="$ROOT_DIR/evaluation/bounded_history"
CIRCOM="${CIRCOM:-circom}"
SNARKJS="${SNARKJS:-snarkjs}"
NODE="${NODE:-node}"
PTAU="${PTAU:-$ROOT_DIR/pot15_final.ptau}"

if [[ ! -f "$PTAU" ]]; then
  echo "Powers-of-Tau file not found: $PTAU" >&2
  exit 1
fi

mkdir -p "$EVAL_DIR/build" "$EVAL_DIR/inputs" "$EVAL_DIR/results"

for k in 10 15 20; do
  name="bounded_history_k${k}"
  build_dir="$EVAL_DIR/build/k${k}"
  input="$EVAL_DIR/inputs/k${k}_valid.json"
  mkdir -p "$build_dir"

  "$NODE" "$EVAL_DIR/scripts/generate_input.js" "$k" "$input"
  "$CIRCOM" "$EVAL_DIR/circuits/${name}.circom" --r1cs --wasm --sym --inspect -o "$build_dir"
  "$SNARKJS" r1cs info "$build_dir/${name}.r1cs" > "$build_dir/r1cs_info.txt"
  "$SNARKJS" groth16 setup "$build_dir/${name}.r1cs" "$PTAU" "$build_dir/${name}_0000.zkey"
  "$SNARKJS" zkey contribute "$build_dir/${name}_0000.zkey" "$build_dir/${name}_final.zkey" \
    --name="bounded-history evaluation k=${k}" -e="bounded-history-k-${k}-local-evaluation"
  "$SNARKJS" zkey export verificationkey "$build_dir/${name}_final.zkey" "$build_dir/${name}_vk.json"
done

echo "Build completed. Run scripts/benchmark_variants.py next."
