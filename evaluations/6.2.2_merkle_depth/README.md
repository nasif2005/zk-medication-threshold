# Section 6.2.2 — Effect of Merkle-tree depth

This directory is reserved for the revised, reproducible depth evaluation.  It holds bounded history at k=10 and varies only the private Poseidon Merkle authentication path across depths 2, 4, 8, and 16.  Legacy depth experiments remain outside this directory and must not be overwritten.

Build with `scripts/build_variants.sh`, then measure with `scripts/benchmark_variants.py --runs 30 --warmups 5`.

Fixed values: k=10, qCurrent=10, Tcurrent=100, mq=60, W=30. Only depth changes.
