pragma circom 2.0.0;
include "threshold_state_transition.circom";
component main {public [qCurrent, Tcurrent, mq, W, med, rootPub, commitCurrPub, nfPrevPub]} = ThresholdStateTransition(20, 16, 21);
