# Section 6.3 - Privacy Quantification

This experiment evaluates centralized plaintext, trusted encrypted-database, and zk-SNARK hidden-state enforcement over exactly the same seeded medication histories.

The common sensitive variable is `X = sum(q_i * 1[T_current-W < t_i <= T_current])`. The primary configuration matches Section 6.2.3: `k=10`, `q_current=10`, `T_current=100`, `m_q=60`, `W=30`, and medication identifier `42`. Only prior histories vary.

Run `python scripts/run_experiment.py`. Defaults are 10,000 histories and seed `20260813`; use `--samples` and `--seed` to override them.

Outputs:

- `workload/shared_histories.csv`: the common input population.
- `workload/metadata.json`: seed, sample count, parameters, and X definition.
- `results/architecture_observations.csv`: each architecture's observable Y for every history.
- `results/privacy_metrics.csv`: scalar ALI, empirical MI, expected ASP, prior ASP, and ASP advantage.
- `results/privacy_performance_tradeoff.csv`: privacy results joined with Section 6.2.3 latency.
- `results/summary.json`: machine-readable summary.

ALI is one when exact X is directly available and zero otherwise. The encrypted-database observer is inside the trusted decryption boundary. The zk view contains fixed public request/policy inputs and the authorization outcome. Proofs, commitments, roots, and nullifiers are excluded from categorical MI estimation: opaque but unique encodings would otherwise behave as sample identifiers and create a misleading estimate.

Section 6.2.3 has no measured trusted encrypted-database latency, so that value is reported as `not_measured` rather than imputed.
