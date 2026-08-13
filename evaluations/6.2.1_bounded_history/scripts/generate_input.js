#!/usr/bin/env node

/* Generate a deterministic valid input for one bounded-history configuration. */
const fs = require("fs");
const path = require("path");
const { buildPoseidon } = require("circomlibjs");

function fail(message) {
  console.error(`Error: ${message}`);
  process.exit(1);
}

async function main() {
  const k = Number(process.argv[2]);
  const outputPath = process.argv[3];
  if (!Number.isInteger(k) || k < 3 || !outputPath) {
    fail("usage: node generate_input.js <k>=10|15|20 <output.json>");
  }

  const poseidon = await buildPoseidon();
  const F = poseidon.F;
  const h2 = (a, b) => BigInt(F.toString(poseidon([a, b])));

  function commitState(tag, med, historyQ, historyT, rho, randomness) {
    let state = h2(tag, med);
    for (let i = 0; i < historyQ.length; i += 1) {
      state = h2(state, historyQ[i]);
      state = h2(state, historyT[i]);
    }
    return h2(h2(state, rho), randomness);
  }

  const tagPatientMed = 123456789n;
  const med = 42n;
  const rhoPrev = 777n;
  const rhoCurr = 888n;
  const rPrev = 1001n;
  const rCurr = 1002n;
  const qCurrent = 10n;
  const Tcurrent = 100n;
  const mq = 60n;
  const W = 30n;

  // Two active entries, one expired occupied entry, then canonical empty slots.
  const historyPrevQ = [20n, 15n, 5n, ...Array(k - 3).fill(0n)];
  const historyPrevT = [90n, 80n, 60n, ...Array(k - 3).fill(0n)];
  const idx = 2n; // Overwrite the expired (5, 60) entry.
  const historyCurrQ = [...historyPrevQ];
  const historyCurrT = [...historyPrevT];
  historyCurrQ[Number(idx)] = qCurrent;
  historyCurrT[Number(idx)] = Tcurrent;

  const activeSum = 20n + 15n;
  if (activeSum + qCurrent > mq) fail("configured workload violates the threshold");

  const commitPrev = commitState(tagPatientMed, med, historyPrevQ, historyPrevT, rhoPrev, rPrev);
  const commitCurr = commitState(tagPatientMed, med, historyCurrQ, historyCurrT, rhoCurr, rCurr);
  const nfPrev = h2(tagPatientMed, rhoPrev);
  const pathElements = [222222n, 333333n];
  const pathIndex = [0n, 0n];
  const rootPub = h2(h2(commitPrev, pathElements[0]), pathElements[1]);

  const stringify = (value) => value.toString();
  const input = {
    qCurrent: stringify(qCurrent), Tcurrent: stringify(Tcurrent), mq: stringify(mq), W: stringify(W), med: stringify(med),
    rootPub: stringify(rootPub), commitCurrPub: stringify(commitCurr), nfPrevPub: stringify(nfPrev),
    idx: stringify(idx), tagPatientMed: stringify(tagPatientMed), rhoPrev: stringify(rhoPrev), rhoCurr: stringify(rhoCurr),
    rPrev: stringify(rPrev), rCurr: stringify(rCurr),
    historyPrevQ: historyPrevQ.map(stringify), historyPrevT: historyPrevT.map(stringify),
    historyCurrQ: historyCurrQ.map(stringify), historyCurrT: historyCurrT.map(stringify),
    pathElements: pathElements.map(stringify), pathIndex: pathIndex.map(stringify)
  };

  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, `${JSON.stringify(input, null, 2)}\n`);
  console.log(`Wrote valid k=${k} workload to ${outputPath}`);
}

main().catch((error) => fail(error.stack || error.message));
