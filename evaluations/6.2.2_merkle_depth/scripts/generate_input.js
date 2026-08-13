#!/usr/bin/env node
const fs=require('fs'),path=require('path'); const {buildPoseidon}=require('circomlibjs');
async function main(){
 const d=Number(process.argv[2]),out=process.argv[3]; if(![2,4,8,16].includes(d)||!out) throw Error('usage: generate_input.js <2|4|8|16> <output>');
 const p=await buildPoseidon(),F=p.F,h=(a,b)=>BigInt(F.toString(p([a,b]))),s=x=>x.toString();
 const tag=123456789n,med=42n,rhoPrev=777n,rhoCurr=888n,rPrev=1001n,rCurr=1002n,qCurrent=10n,Tcurrent=100n,mq=60n,W=30n,idx=2n;
 const pq=[20n,15n,5n,...Array(7).fill(0n)],pt=[90n,80n,60n,...Array(7).fill(0n)],cq=[...pq],ct=[...pt]; cq[2]=qCurrent;ct[2]=Tcurrent;
 function commit(q,t,rho,r){let x=h(tag,med);for(let i=0;i<10;i++){x=h(x,q[i]);x=h(x,t[i]);}return h(h(x,rho),r);}
 const prev=commit(pq,pt,rhoPrev,rPrev),curr=commit(cq,ct,rhoCurr,rCurr),pe=Array.from({length:d},(_,i)=>222222n+BigInt(i)),pi=Array(d).fill(0n);let root=prev;for(const e of pe)root=h(root,e);
 const data={qCurrent:s(qCurrent),Tcurrent:s(Tcurrent),mq:s(mq),W:s(W),med:s(med),rootPub:s(root),commitCurrPub:s(curr),nfPrevPub:s(h(tag,rhoPrev)),idx:s(idx),tagPatientMed:s(tag),rhoPrev:s(rhoPrev),rhoCurr:s(rhoCurr),rPrev:s(rPrev),rCurr:s(rCurr),historyPrevQ:pq.map(s),historyPrevT:pt.map(s),historyCurrQ:cq.map(s),historyCurrT:ct.map(s),pathElements:pe.map(s),pathIndex:pi.map(s)};
 fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(data,null,2)+'\n');console.log(`Wrote depth ${d}: ${out}`);
} main().catch(e=>{console.error(e);process.exit(1)});
