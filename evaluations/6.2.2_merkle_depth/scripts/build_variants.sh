#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"; EVAL="$ROOT/evaluations/6.2.2_merkle_depth"; PTAU="${PTAU:-$ROOT/shared/ptau/powersOfTau28_hez_final_17.ptau}"
[[ -f "$PTAU" ]] || { echo "Missing PTAU: $PTAU" >&2; exit 1; }; mkdir -p "$EVAL"/{build,inputs,results}
for d in 2 4 8 16; do
 n="merkle_depth_d$d"; b="$EVAL/build/d$d"; mkdir -p "$b"; node "$EVAL/scripts/generate_input.js" "$d" "$EVAL/inputs/d${d}_valid.json"
 circom "$EVAL/circuits/$n.circom" --r1cs --wasm --sym --inspect -o "$b"; snarkjs r1cs info "$b/$n.r1cs" > "$b/r1cs_info.txt"
 snarkjs groth16 setup "$b/$n.r1cs" "$PTAU" "$b/${n}_0000.zkey"
 snarkjs zkey contribute "$b/${n}_0000.zkey" "$b/${n}_final.zkey" --name="depth d=$d" -e="merkle-depth-d-$d"
 snarkjs zkey export verificationkey "$b/${n}_final.zkey" "$b/${n}_vk.json"; snarkjs zkey verify "$b/$n.r1cs" "$PTAU" "$b/${n}_final.zkey"
done
echo 'Everything went okay'
