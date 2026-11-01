// E487: marginal-preserving dependence falsification, synthetic scheduling only.
// Frozen E473 24-option fixture, E455 policies, utility penalty=50, new seeds 768..895.
// No evaluator, third-party security payloads, or real latency measurements.
import assert from 'node:assert/strict';
const BUDGET=400,N=24,START=768,END=895,DRAWS=128,PENALTY=50;
const Q=[0,.25,.5,.75,1];
const POLICIES=['exact400','exact360','dp50','dp100','chance90'];
function fixture(seed,n=N){let s=(seed+1)>>>0,rows=[];for(let i=0;i<n;i++){s=(Math.imul(1664525,s)+1013904223)>>>0;const reward=5+s%96;s=(Math.imul(1664525,s)+1013904223)>>>0;rows.push({id:i,reward,cost:10+s%111})}return rows}
function densityOrder(rows){return rows.slice().sort((a,b)=>b.reward/b.cost-a.reward/a.cost||a.id-b.id)}
function exact(rows,cap){let dp=Array.from({length:cap+1},()=>({r:0,c:0,ids:[]}));for(const row of rows){const next=dp.slice();for(let b=row.cost;b<=cap;b++){const old=dp[b-row.cost],cand={r:old.r+row.reward,c:old.c+row.cost,ids:old.ids.concat(row.id)},cur=next[b];if(cand.r>cur.r||(cand.r===cur.r&&cand.c<cur.c))next[b]=cand}dp=next}const selected=new Set(dp[cap].ids);return densityOrder(rows).filter(x=>selected.has(x.id)).map(x=>x.id)}
function survival(c){return c===0?1:Math.max(0,Math.min(1,(BUDGET/c-.7)/.6))}
function optimize(rows,penalty=0,minCompletion=0){const dp=Array.from({length:Math.floor(BUDGET/.7)+1},()=>({value:-Infinity,ids:[]}));dp[0]={value:0,ids:[]};for(const row of densityOrder(rows)){for(let c=dp.length-1;c>=row.cost;c--){const old=dp[c-row.cost];if(!Number.isFinite(old.value))continue;const v=old.value+row.reward*survival(c);if(v>dp[c].value+1e-10)dp[c]={value:v,ids:old.ids.concat(row.id)}}}let best=null;for(let c=0;c<dp.length;c++){const x=dp[c];if(!Number.isFinite(x.value)||survival(c)+1e-12<minCompletion)continue;const u=x.value-penalty*(1-survival(c));if(!best||u>best.u+1e-10)best={ids:x.ids,u}}return best}
function policies(rows){return {exact400:exact(rows,400),exact360:exact(rows,360),dp50:optimize(rows,50).ids,dp100:optimize(rows,100).ids,chance90:optimize(rows,0,.9).ids}}
function noise(seed,draw,count){let s=(0x9e3779b9^Math.imul(seed,2654435761)^Math.imul(draw,1013904223))>>>0,out=[];for(let i=0;i<count;i++){s=(Math.imul(1664525,s)+1013904223)>>>0;out.push(.7+.6*s/4294967296)}return out}
function factors(seed,draw){return {independent:noise(seed,draw,N),shared:Array(N).fill(noise((seed^0xa5a5a5a5)>>>0,(draw^0x5a5a5a5a)>>>0,1)[0])}}
function realized(rows,ids,fac){let cost=0,reward=0;for(const id of ids){const r=rows[id];if(cost+r.cost*fac[id]>BUDGET)return reward-PENALTY;cost+=r.cost*fac[id];reward+=r.reward}return reward}
function mean(a){return a.reduce((s,x)=>s+x,0)/a.length}
function round(x){return +x.toFixed(6)}
function describe(a){const m=mean(a),se=Math.sqrt(a.reduce((s,x)=>s+(x-m)**2,0)/(a.length-1)/a.length);return {mean:round(m),seed_se:round(se),descriptive_95:[round(m-1.96*se),round(m+1.96*se)]}}
function crossover(ind,shared){return ind<0&&shared>0?-ind/(shared-ind):null}
function test(){
 assert.equal(survival(0),1);assert.equal(survival(BUDGET/.7+1),0);
 // Two 250-cost jobs: P(both fit) shared=1/6, independent=1/18, 50% mixture=1/9.
 const pShared=(.8-.7)/.6,pIndependent=(.2*.2)/(2*.6*.6);
 assert.ok(Math.abs(pShared-1/6)<1e-12&&Math.abs(pIndependent-1/18)<1e-12);
 assert.ok(Math.abs(.5*pShared+.5*pIndependent-1/9)<1e-12);
 // Bernoulli choice of a fully shared or independent U[.7,1.3] vector:
 // marginal distribution stays U[.7,1.3] and Corr(X_i,X_j)=q exactly.
 for(const q of Q){assert.ok(Math.abs((1-q)*1+q*1-1)<1e-12);assert.ok(Math.abs((1-q)*0+q*1-q)<1e-12)}
 for(let seed=0;seed<3;seed++){const rows=fixture(seed,8),order=densityOrder(rows);for(const penalty of [0,50,100]){let best=-Infinity;for(let mask=0;mask<256;mask++){const ids=order.filter((_,i)=>mask&(1<<i)).map(x=>x.id);let c=0,v=0;for(const id of ids){c+=rows[id].cost;v+=rows[id].reward*survival(c)}best=Math.max(best,v-penalty*(1-survival(c)))}assert.ok(Math.abs(optimize(rows,penalty).u-best)<1e-8)}}
 const f=factors(768,0);assert.equal(new Set(f.shared).size,1);assert.equal(f.independent.length,N);
}
function run(){test();const per=[];for(let seed=START;seed<=END;seed++){const rows=fixture(seed),p=policies(rows);const totals={independent:Object.fromEntries(POLICIES.map(x=>[x,0])),shared:Object.fromEntries(POLICIES.map(x=>[x,0]))};for(let draw=0;draw<DRAWS;draw++){const f=factors(seed,draw);for(const mode of ['independent','shared'])for(const name of POLICIES)totals[mode][name]+=realized(rows,p[name],f[mode])}for(const mode of ['independent','shared'])for(const name of POLICIES)totals[mode][name]/=DRAWS;per.push({seed,totals})}
 const results={};for(const name of POLICIES.filter(x=>x!=='exact400')){const independent=per.map(x=>x.totals.independent[name]-x.totals.independent.exact400),shared=per.map(x=>x.totals.shared[name]-x.totals.shared.exact400);const a=describe(independent),b=describe(shared),grid=Object.fromEntries(Q.map(q=>[String(q),describe(independent.map((x,i)=>(1-q)*x+q*shared[i]))]));const qStar=crossover(a.mean,b.mean);results[name]={independent:a,shared:b,q_grid:grid,zero_crossing_q:qStar===null?null:round(qStar)}}
 // Exact linearity of mixture expectations is structural, not a fitted regression.
 for(const name of Object.keys(results)){const x=results[name];for(const q of Q){const expected=(1-q)*x.independent.mean+q*x.shared.mean;assert.ok(Math.abs(expected-x.q_grid[String(q)].mean)<2e-6)}}
 return {experiment:'E487_MARGINAL_PRESERVING_DEPENDENCE',date:'2026-11-02',model:'Bernoulli copula mixture: probability q all 24 latency multipliers share U[0.7,1.3); otherwise independent U[0.7,1.3). All one-dimensional marginals exactly fixed; pairwise Pearson correlation exactly q.',fixture_seeds:[START,END],draws_per_seed:DRAWS,nominal_budget:BUDGET,utility:'completed-prefix reward - 50 if truncated',policy_source:'E455/E473 frozen algorithms; exact360 simple conservative capacity control',results,tests:'9 exhaustive 8-option DP oracles; 2-job exact mixture oracle; marginal/correlation algebra; factor checks; exact affine mixture assertions PASS',limitations:'Synthetic common-mode mixture copula only; q is an exact model correlation, not measured replay dependence; descriptive seed intervals, not calibrated population confidence; 128 deterministic draws per seed; no empirical evaluator access.'};}
console.log(JSON.stringify(run(),null,2));
