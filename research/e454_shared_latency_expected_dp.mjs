// E454: synthetic abstract scheduling, NOT a security exploit or production policy.
// Fixed 128-seed control and independent 128-seed holdout; 64 draws/seed.
const BUDGET=400,N=24,DRAWS=Array.from({length:64},(_,i)=>i);

function fixture(seed,n=N){let state=(seed+1)>>>0,rows=[];for(let i=0;i<n;i++){state=(Math.imul(1664525,state)+1013904223)>>>0;let reward=5+state%96;state=(Math.imul(1664525,state)+1013904223)>>>0;rows.push({id:i,reward,cost:10+state%111})}return rows}

function densityOrder(rows){return rows.slice().sort((a,b)=>(b.reward/b.cost)-(a.reward/a.cost)||a.id-b.id)}

function greedy(rows,cap){let left=cap,out=[];for(const c of densityOrder(rows)){if(c.cost<=left){out.push(c.id);left-=c.cost}}return out}

function exact(rows,cap){let dp=Array.from({length:cap+1},()=>({r:0,c:0,ids:[]}));for(const row of rows){let next=dp.slice();for(let b=row.cost;b<=cap;b++){let old=dp[b-row.cost],cand={r:old.r+row.reward,c:old.c+row.cost,ids:old.ids.concat(row.id)},cur=next[b];if(cand.r>cur.r||(cand.r===cur.r&&cand.c<cur.c))next[b]=cand}dp=next}let selected=new Set(dp[cap].ids);return densityOrder(rows).filter(x=>selected.has(x.id)).map(x=>x.id)}

function latencyNoise(seed,draw,count){let state=(0x9e3779b9^Math.imul(seed,2654435761)^Math.imul(draw,1013904223))>>>0;let out=[];for(let i=0;i<count;i++){state=(Math.imul(1664525,state)+1013904223)>>>0;out.push(.7+.6*state/4294967296)}return out}

function factors(seed,draw,count,mode){let indep=latencyNoise(seed,draw,count),common=latencyNoise((seed^0xa5a5a5a5)>>>0,(draw^0x5a5a5a5a)>>>0,1)[0];if(mode==="independent")return indep;if(mode==="fully_shared")return Array(count).fill(common);return indep.map(x=>(x+common)/2)}

function realized(rows,ids,f){let cost=0,reward=0;for(const id of ids){let r=rows[id];if(cost+r.cost*f[id]>BUDGET)return {reward,truncated:1};cost+=r.cost*f[id];reward+=r.reward}return {reward,truncated:0}}

function survival(cost){if(cost===0)return 1;return Math.max(0,Math.min(1,(BUDGET/cost-.7)/.6))}

function analytic(rows,ids){let cost=0,value=0;for(const id of ids){cost+=rows[id].cost;value+=rows[id].reward*survival(cost)}return value}

function sharedDP(rows){let order=densityOrder(rows),maxCost=Math.floor(BUDGET/.7);let dp=Array.from({length:maxCost+1},()=>({value:-Infinity,ids:[]}));dp[0]={value:0,ids:[]};for(const row of order){for(let c=maxCost;c>=row.cost;c--){let old=dp[c-row.cost];if(!Number.isFinite(old.value))continue;let value=old.value+row.reward*survival(c);if(value>dp[c].value+1e-10)dp[c]={value,ids:old.ids.concat(row.id)}}}let best=dp[0];for(let c=1;c<=maxCost;c++)if(dp[c].value>best.value+1e-10)best=dp[c];return best}

function evaluateSeeds(start){let modes=["independent","half_shared","fully_shared"],names=["greedy100","exact100","greedy85","exact85","sharedDP"],sum=Object.fromEntries(modes.map(m=>[m,Object.fromEntries(names.map(n=>[n,{reward:0,trunc:0}]))])),analyticSum=Object.fromEntries(names.map(n=>[n,0])),seedDeltas=Object.fromEntries(modes.map(m=>[m,[]]));for(let seed=start;seed<start+128;seed++){let rows=fixture(seed),dp=sharedDP(rows),ids={greedy100:greedy(rows,400),exact100:exact(rows,400),greedy85:greedy(rows,340),exact85:exact(rows,340),sharedDP:dp.ids};if(Math.abs(analytic(rows,dp.ids)-dp.value)>1e-7)throw Error("DP analytic mismatch");for(const n of names)analyticSum[n]+=analytic(rows,ids[n]);let per=Object.fromEntries(modes.map(m=>[m,0]));for(const draw of DRAWS){for(const mode of modes){let f=factors(seed,draw,N,mode),obs={};for(const n of names){let v=realized(rows,ids[n],f);sum[mode][n].reward+=v.reward;sum[mode][n].trunc+=v.truncated;obs[n]=v.reward}per[mode]+=obs.sharedDP-obs.exact100}}for(const m of modes)seedDeltas[m].push(per[m]/64)}return {seed_range:[start,start+127],analytic_shared_expectations:Object.fromEntries(names.map(n=>[n,analyticSum[n]/128])),modes:Object.fromEntries(modes.map(m=>[m,{policies:Object.fromEntries(names.map(n=>[n,{mean_reward:sum[m][n].reward/8192,truncation_rate:sum[m][n].trunc/8192}])),sharedDP_minus_exact100:seedDeltas[m].reduce((a,b)=>a+b,0)/128,paired_seed_wins_losses_ties:[seedDeltas[m].filter(x=>x>0).length,seedDeltas[m].filter(x=>x<0).length,seedDeltas[m].filter(x=>x===0).length]}]))}}

function runTests(){for(let seed=0;seed<4;seed++){let rows=fixture(seed,8),order=densityOrder(rows),best=-1;for(let mask=0;mask<256;mask++){let ids=order.filter((_,i)=>(mask&(1<<i))!==0).map(x=>x.id);best=Math.max(best,analytic(rows,ids))}let actual=sharedDP(rows);if(Math.abs(best-actual.value)>1e-8)throw Error("DP exhaustive mismatch "+seed)}if(Math.abs(survival(400/1.3)-1)>1e-12)throw Error("survival upper");if(survival(400/.7+1e-4)!==0)throw Error("survival lower");let control=evaluateSeeds(128);let expected=[642.4522705078125,639.470703125,623.5400390625,624.3951416015625];let actual=[control.modes.independent.policies.greedy100.mean_reward,control.modes.independent.policies.exact100.mean_reward,control.modes.fully_shared.policies.greedy100.mean_reward,control.modes.fully_shared.policies.exact100.mean_reward];if(actual.some((v,i)=>Math.abs(v-expected[i])>1e-9))throw Error("E441 exact baseline mismatch "+JSON.stringify(actual));return control}

const control=runTests();
const holdout=evaluateSeeds(256);
console.log(JSON.stringify({experiment:"E454_SHARED_LATENCY_EXPECTED_PREFIX_DP",model:"fully shared U[0.7,1.3) synthetic multipliers; no real replay",tests:"4 exhaustive 8-option DP controls, 2 survival boundaries, 4 exact E441 baseline means PASS",control,holdout},null,2));
