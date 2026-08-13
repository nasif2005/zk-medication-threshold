# Section 6.2.3 — Computational overhead of privacy preservation

This experiment compares the exact fixed workload used for the revised zk experiment (k=10, Merkle depth=2) with a plaintext rolling-window threshold check. The zk timing includes witness generation, Groth16 proving, and verification. Trusted setup and circuit compilation are excluded as one-time preprocessing.
