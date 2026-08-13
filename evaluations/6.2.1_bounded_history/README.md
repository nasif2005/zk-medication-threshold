# Section 6.2.1 - Effect of Bounded-History Capacity k

This directory is the reproducible source of truth for the revised bounded-history experiment. It does not alter legacy artifacts in the resource root.

## Layout

- `circuits/`: one canonical range-constrained relation and three thin k-specific wrappers.
- `scripts/generate_input.js`: creates deterministic valid workloads with two active records and one expired record.
- `scripts/build_variants.sh`: compiles each circuit, records R1CS information, and creates Groth16 parameters.
- `scripts/benchmark_variants.py`: executes warm-ups and 30 measured witness/prove/verify runs per configuration.
- `inputs/`: generated witnesses in JSON form.
- `build/`: generated compiler and proving artifacts; do not edit manually.
- `results/`: raw CSV measurements, summaries, environment metadata, and proof artifacts.

## Linux execution

Run from the `paper5 resource` directory after installing the pinned Node dependencies:

```bash
npm install
chmod +x evaluation/bounded_history/scripts/build_variants.sh
./evaluation/bounded_history/scripts/build_variants.sh
python3 evaluation/bounded_history/scripts/benchmark_variants.py --runs 30 --warmups 5
```

Set `CIRCOM`, `SNARKJS`, `NODE`, or `PTAU` before the build command if they are not on `PATH` or if the Powers-of-Tau file is stored elsewhere.

## Measurement boundary

Circuit compilation and Groth16 setup are build-time costs and are excluded from online request latency. Each recorded request generates a witness, creates a Groth16 proof, and verifies it in a fresh command invocation. The benchmark preserves every raw observation and reports mean, standard deviation, median, minimum, and maximum.
