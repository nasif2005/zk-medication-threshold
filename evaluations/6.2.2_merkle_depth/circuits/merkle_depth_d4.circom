pragma circom 2.0.0;
include "threshold_state_transition.circom";
component main {public [qCurrent,Tcurrent,mq,W,med,rootPub,commitCurrPub,nfPrevPub]} = ThresholdStateTransition(10,4,16,21);
