pragma circom 2.0.0;

include "../../../node_modules/circomlib/circuits/comparators.circom";
include "../../../node_modules/circomlib/circuits/bitify.circom";
include "../../../node_modules/circomlib/circuits/poseidon.circom";

/*
 * Canonical circuit for Section 6.2.1.
 *
 * This relation proves a policy-compliant transition from a Merkle-authenticated
 * predecessor state to a successor state. The history capacity k is a compile-time
 * parameter; all other logic is identical across the k=10,15,20 experiments.
 */
template ThresholdStateTransition(k, depth, nBits, sumBits) {
    // Public request and verification context.
    signal input qCurrent;
    signal input Tcurrent;
    signal input mq;
    signal input W;
    signal input med;
    signal input rootPub;
    signal input commitCurrPub;
    signal input nfPrevPub;

    // Private witness.
    signal input idx;
    signal input tagPatientMed;
    signal input rhoPrev;
    signal input rhoCurr;
    signal input rPrev;
    signal input rCurr;
    signal input historyPrevQ[k];
    signal input historyPrevT[k];
    signal input historyCurrQ[k];
    signal input historyCurrT[k];
    signal input pathElements[depth];
    signal input pathIndex[depth];

    signal age[k];
    signal isOccupied[k];
    signal isWithinWindow[k];
    signal isActive[k];
    signal maskedQ[k];
    signal isIdx[k];
    signal selectedActive[k];
    signal prevState[2 * k + 1];
    signal currState[2 * k + 1];
    signal commitPrev;
    signal commitCurr;
    signal nfPrev;
    signal activeSum;
    signal total;

    component prevQBits[k];
    component prevTBits[k];
    component currQBits[k];
    component currTBits[k];
    component qZero[k];
    component tZero[k];
    component tLeqNow[k];
    component ageLtW[k];
    component eq[k];
    component prevHashQ[k];
    component prevHashT[k];
    component currHashQ[k];
    component currHashT[k];

    component qCurrentBits = Num2Bits(nBits);
    component tCurrentBits = Num2Bits(nBits);
    component mqBits = Num2Bits(nBits);
    component wBits = Num2Bits(nBits);
    component totalBits = Num2Bits(sumBits);

    qCurrentBits.in <== qCurrent;
    tCurrentBits.in <== Tcurrent;
    mqBits.in <== mq;
    wBits.in <== W;

    var i;
    for (i = 0; i < k; i++) {
        // Explicit integer-domain bounds required by the policy relation.
        prevQBits[i] = Num2Bits(nBits);
        prevQBits[i].in <== historyPrevQ[i];
        prevTBits[i] = Num2Bits(nBits);
        prevTBits[i].in <== historyPrevT[i];
        currQBits[i] = Num2Bits(nBits);
        currQBits[i].in <== historyCurrQ[i];
        currTBits[i] = Num2Bits(nBits);
        currTBits[i].in <== historyCurrT[i];

        // Canonical empty slot: (q_i = 0) iff (t_i = 0).
        qZero[i] = IsZero();
        qZero[i].in <== historyPrevQ[i];
        tZero[i] = IsZero();
        tZero[i].in <== historyPrevT[i];
        qZero[i].out === tZero[i].out;
        isOccupied[i] <== 1 - qZero[i].out;

        // Historical timestamps must not lie in the future.
        tLeqNow[i] = LessEqThan(nBits);
        tLeqNow[i].in[0] <== historyPrevT[i];
        tLeqNow[i].in[1] <== Tcurrent;
        tLeqNow[i].out === 1;

        age[i] <== Tcurrent - historyPrevT[i];
        ageLtW[i] = LessThan(nBits);
        ageLtW[i].in[0] <== age[i];
        ageLtW[i].in[1] <== W;
        isWithinWindow[i] <== ageLtW[i].out;
        isActive[i] <== isOccupied[i] * isWithinWindow[i];
        maskedQ[i] <== historyPrevQ[i] * isActive[i];

        eq[i] = IsEqual();
        eq[i].in[0] <== idx;
        eq[i].in[1] <== i;
        isIdx[i] <== eq[i].out;
        selectedActive[i] <== isIdx[i] * isActive[i];

        // Exactly the selected slot receives the current event.
        historyCurrQ[i] === historyPrevQ[i] + isIdx[i] * (qCurrent - historyPrevQ[i]);
        historyCurrT[i] === historyPrevT[i] + isIdx[i] * (Tcurrent - historyPrevT[i]);
    }

    signal partial[k + 1];
    signal idxPartial[k + 1];
    signal selectedActivePartial[k + 1];
    partial[0] <== 0;
    idxPartial[0] <== 0;
    selectedActivePartial[0] <== 0;
    for (i = 0; i < k; i++) {
        partial[i + 1] <== partial[i] + maskedQ[i];
        idxPartial[i + 1] <== idxPartial[i] + isIdx[i];
        selectedActivePartial[i + 1] <== selectedActivePartial[i] + selectedActive[i];
    }

    activeSum <== partial[k];
    total <== activeSum + qCurrent;
    totalBits.in <== total;

    component totalLeq = LessEqThan(sumBits);
    totalLeq.in[0] <== total;
    totalLeq.in[1] <== mq;
    totalLeq.out === 1;

    // Exactly one update slot, and it must be inactive.
    idxPartial[k] === 1;
    selectedActivePartial[k] === 0;

    // Commit(tag, medication, ordered history, state nonce, commitment randomness).
    component initPrev = Poseidon(2);
    initPrev.inputs[0] <== tagPatientMed;
    initPrev.inputs[1] <== med;
    prevState[0] <== initPrev.out;
    component initCurr = Poseidon(2);
    initCurr.inputs[0] <== tagPatientMed;
    initCurr.inputs[1] <== med;
    currState[0] <== initCurr.out;

    for (i = 0; i < k; i++) {
        prevHashQ[i] = Poseidon(2);
        prevHashQ[i].inputs[0] <== prevState[2 * i];
        prevHashQ[i].inputs[1] <== historyPrevQ[i];
        prevState[2 * i + 1] <== prevHashQ[i].out;
        prevHashT[i] = Poseidon(2);
        prevHashT[i].inputs[0] <== prevState[2 * i + 1];
        prevHashT[i].inputs[1] <== historyPrevT[i];
        prevState[2 * i + 2] <== prevHashT[i].out;

        currHashQ[i] = Poseidon(2);
        currHashQ[i].inputs[0] <== currState[2 * i];
        currHashQ[i].inputs[1] <== historyCurrQ[i];
        currState[2 * i + 1] <== currHashQ[i].out;
        currHashT[i] = Poseidon(2);
        currHashT[i].inputs[0] <== currState[2 * i + 1];
        currHashT[i].inputs[1] <== historyCurrT[i];
        currState[2 * i + 2] <== currHashT[i].out;
    }

    signal prevWithRho;
    signal currWithRho;
    component prevRhoHash = Poseidon(2);
    prevRhoHash.inputs[0] <== prevState[2 * k];
    prevRhoHash.inputs[1] <== rhoPrev;
    prevWithRho <== prevRhoHash.out;
    component currRhoHash = Poseidon(2);
    currRhoHash.inputs[0] <== currState[2 * k];
    currRhoHash.inputs[1] <== rhoCurr;
    currWithRho <== currRhoHash.out;

    component finalPrev = Poseidon(2);
    finalPrev.inputs[0] <== prevWithRho;
    finalPrev.inputs[1] <== rPrev;
    commitPrev <== finalPrev.out;
    component finalCurr = Poseidon(2);
    finalCurr.inputs[0] <== currWithRho;
    finalCurr.inputs[1] <== rCurr;
    commitCurr <== finalCurr.out;
    commitCurr === commitCurrPub;

    component nullifierHash = Poseidon(2);
    nullifierHash.inputs[0] <== tagPatientMed;
    nullifierHash.inputs[1] <== rhoPrev;
    nfPrev <== nullifierHash.out;
    nfPrev === nfPrevPub;

    // Private Poseidon Merkle authentication path parameterized by depth.
    signal merkleNode[depth + 1];
    signal merkleLeft[depth];
    signal merkleRight[depth];
    component merkleHash[depth];
    merkleNode[0] <== commitPrev;
    for (i = 0; i < depth; i++) {
        pathIndex[i] * (pathIndex[i] - 1) === 0;
        merkleLeft[i] <== merkleNode[i] + pathIndex[i] * (pathElements[i] - merkleNode[i]);
        merkleRight[i] <== pathElements[i] + pathIndex[i] * (merkleNode[i] - pathElements[i]);
        merkleHash[i] = Poseidon(2);
        merkleHash[i].inputs[0] <== merkleLeft[i];
        merkleHash[i].inputs[1] <== merkleRight[i];
        merkleNode[i + 1] <== merkleHash[i].out;
    }
    merkleNode[depth] === rootPub;
}
