# Medication Threshold Evaluation Package

This directory contains the reproducible evaluation materials for *A Privacy-Preserving Cryptographic Framework for Medication Threshold Enforcement*.

## Active materials

- `evaluations/6.2.1_bounded_history/` — bounded-history-size experiment (`k = 10, 15, 20`).
- `evaluations/6.2.2_merkle_depth/` — Merkle-tree-depth experiment (`d = 2, 4, 8, 16`).
- `evaluations/6.2.3_privacy_overhead/` — privacy-overhead experiment.
- `shared/` — shared trusted setup and environment information.

Each evaluation directory keeps its circuits or scripts, generated build artefacts where required, raw measurements, and summary results together.

## Rebuilding dependencies

`node_modules/` is deliberately excluded because it is generated from `package.json` and `package-lock.json`. Run `npm install` in this directory before rebuilding or rerunning an experiment.

## Legacy snapshot

`legacy/root_legacy_snapshot/` holds superseded prototypes, old build outputs, duplicate setup files, and earlier layouts moved out of the active working area. It is retained for traceability and is not part of the current evaluation package.
