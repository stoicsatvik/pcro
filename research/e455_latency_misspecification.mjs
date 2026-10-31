// E455: synthetic abstract scheduling sensitivity, not an evaluator or production policy.
// Falsifiable question: does a shared-latency expected-prefix policy survive
// distribution misspecification and an explicit full-schedule truncation penalty?
const BUDGET=400;
const round=x=>Number(x.toFixed(6));
function fixture(seed,n=24,family='lcg') {
  let s=(seed+1)>>>0, out=[];
  for(let i=0;i<n;i++) {
    if(family==='lcg') {
      s=(Math.imul(1664525,s)+1013904223)>>>0; const reward=5+s%96;
      s=(Math.imul(1664525,s)+1013904223)>>>0;
      out.push({id:i,reward,cost:10+s%111});
    } else {
      s^=s<<13;s^=s>>>17;s^=s<<5;s>>>=0;const reward=2+s%99;
      s^=s<<13;s^=s>>>17;s^=s<<5;s>>>=0;
      out.push({id:i,reward,cost:8+s%123});
    }
  }
  return out;
}
const density=rows=>rows.slice().sort((a,b)=>b.reward/b.cost-a.reward/a.cost||a.id-b.id);
function nominalExact(rows,cap=BUDGET){
  let dp=Array.from({length:cap+1},()=>({reward:0,cost:0,ids:[]}));
  for(const row of rows){const next=dp.slice();for(let b=row.cost;b<=cap;b++){
    const old=dp[b-row.cost],candidate={reward:old.reward+row.reward,cost:old.cost+row.cost,ids:old.ids.concat(row.id)},cur=next[b];
    if(candidate.reward>cur.reward||(candidate.reward===cur.reward&&candidate.cost<cur.cost))next[b]=candidate;
  }dp=next;}
  const chosen=new Set(dp[cap].ids);return density(rows).filter(r=>chosen.has(r.id)).map(r=>r.id);
}
function survival(cost,low,high){if(cost===0)return 1;return Math.max(0,Math.min(1,(BUDGET/cost-low)/(high-low)));}
function objective(rows,ids,low,high,penalty=0){
  let cost=0,reward=0;for(const id of ids){cost+=rows[id].cost;reward+=rows[id].reward*survival(cost,low,high);}
  const completion=survival(cost,low,high);
  return {reward,completion,utility:reward-penalty*(1-completion),nominalCost:cost};
}
function riskDP(rows,penalty,assumedLow=.7,assumedHigh=1.3){
  const maxCost=Math.floor(BUDGET/assumedLow);
  const dp=Array.from({length:maxCost+1},()=>({value:-Infinity,ids:[]}));dp[0]={value:0,ids:[]};
  for(const row of density(rows)){
    for(let c=maxCost;c>=row.cost;c--){const old=dp[c-row.cost];if(!Number.isFinite(old.value))continue;
      const value=old.value+row.reward*survival(c,assumedLow,assumedHigh);
      if(value>dp[c].value+1e-10)dp[c]={value,ids:old.ids.concat(row.id)};
    }
  }
  let best={utility:-Infinity,ids:[]};
  for(let c=0;c<=maxCost;c++)if(Number.isFinite(dp[c].value)){
    const utility=dp[c].value-penalty*(1-survival(c,assumedLow,assumedHigh));
    if(utility>best.utility+1e-10)best={utility,ids:dp[c].ids};
  }
  return best.ids;
}
function test(){
  let count=0;
  for(const penalty of [0,25,100,500])for(let seed=0;seed<4;seed++){
    const rows=fixture(seed,8,'xorshift'),order=density(rows);let optimum=-Infinity;
    for(let mask=0;mask<256;mask++){
      const ids=order.filter((_,i)=>mask&(1<<i)).map(r=>r.id);
      optimum=Math.max(optimum,objective(rows,ids,.7,1.3,penalty).utility);
    }
    const ids=riskDP(rows,penalty);
    if(Math.abs(objective(rows,ids,.7,1.3,penalty).utility-optimum)>1e-8)throw Error('DP exhaustive mismatch '+seed+' '+penalty);
    count++;
  }
  if(survival(BUDGET/1.3,.7,1.3)<1-1e-12||survival(BUDGET/.7+1e-4,.7,1.3)!==0)throw Error('probability boundary');
  count+=2;
  for(let seed=384;seed<388;seed++){
    const rows=fixture(seed);const ids=riskDP(rows,0);
    if(Math.abs(objective(rows,ids,.7,1.3).reward-objective(rows,ids,.7,1.3).utility)>1e-10)throw Error('zero-penalty identity');
    count++;
  }
  // Exact E454 holdout analytic control (256..383), independent of Monte Carlo draws.
  let nominalMean=0, sharedMean=0;
  for(let seed=256;seed<384;seed++){
    const rows=fixture(seed);
    nominalMean+=objective(rows,nominalExact(rows),.7,1.3).reward/128;
    sharedMean+=objective(rows,riskDP(rows,0),.7,1.3).reward/128;
  }
  if(Math.abs(nominalMean-630.789093)>1e-5||Math.abs(sharedMean-658.110632)>1e-5)
    throw Error('E454 holdout analytic control mismatch');
  count+=2;
  return count;
}
const tests=test();
const distributions={assumed:[.7,1.3],slower:[.9,1.5],faster:[.5,1.1]};
const penalties=[0,25,100,500];
const result={experiment:'E455_LATENCY_MISSPECIFICATION_TRUNCATION_PENALTY',scope:'synthetic deterministic analytic expected-prefix reward',tests_passed:tests,groups:{}};
for(const family of ['lcg','xorshift']){
  const seeds=family==='lcg'?Array.from({length:128},(_,i)=>384+i):Array.from({length:128},(_,i)=>1000+i);
  const agg={};for(const [name,[lo,hi]] of Object.entries(distributions)){
    agg[name]={};for(const policy of ['nominal400',...penalties.map(x=>'risk'+x)])agg[name][policy]={reward:0,completion:0,utility100:0,winsVsNominal:0};
  }
  for(const seed of seeds){
    const rows=fixture(seed,24,family),ids={nominal400:nominalExact(rows)};
    for(const p of penalties)ids['risk'+p]=riskDP(rows,p);
    for(const [name,[lo,hi]] of Object.entries(distributions)){
      const baseline=objective(rows,ids.nominal400,lo,hi,100).utility;
      for(const [policy,order] of Object.entries(ids)){
        const x=objective(rows,order,lo,hi,100),a=agg[name][policy];
        a.reward+=x.reward;a.completion+=x.completion;a.utility100+=x.utility;
        if(x.utility>baseline+1e-9)a.winsVsNominal++;
      }
    }
  }
  for(const d of Object.values(agg))for(const a of Object.values(d)){
    a.reward=round(a.reward/seeds.length);a.completion=round(a.completion/seeds.length);
    a.utility100=round(a.utility100/seeds.length);
  }
  result.groups[family]={seeds:[seeds[0],seeds.at(-1)],count:seeds.length,policies:agg};
}
console.log(JSON.stringify(result,null,2));
