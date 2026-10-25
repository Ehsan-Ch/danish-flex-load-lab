import {cost,totals,dailyCSV,policies,names} from './core.mjs';
const $=id=>document.getElementById(id),fmt=(v,n=2)=>v==null?'—':Number(v).toLocaleString('en-GB',{minimumFractionDigits:n,maximumFractionDigits:n}),pct=v=>v==null?'—':fmt(v*100,1)+'%',modelNames={weekly:'Weekly lag',profile:'Recent profile',ridge:'Ridge',boosted:'Boosted',logistic:'Logistic'};
const euros=v=>(v<0?'−':'')+'€'+fmt(Math.abs(v));
const stat=(label,value,note)=>`<article class="stat"><span>${label}</span><strong>${value}</strong><p>${note}</p></article>`;
function endTime(start){const [h,m]=start.split(':').map(Number);return String(h+2).padStart(2,'0')+':'+String(m).padStart(2,'0');}
function plot(actual,predicted,chosen,labels){
 const lo=Math.min(0,...actual,...predicted),hi=Math.max(1,...actual,...predicted),pad=(hi-lo)*.1,min=lo-pad,max=hi+pad;
 const x=i=>50+i*730/40,y=v=>248-(v-min)*220/(max-min),path=a=>a.map((v,i)=>`${i?'L':'M'}${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ');
 let out='';for(let i=0;i<=4;i++){const v=min+(max-min)*i/4;out+=`<line x1="50" x2="780" y1="${y(v)}" y2="${y(v)}" stroke="#e4eae5"/><text x="42" y="${y(v)+4}" text-anchor="end">${fmt(v,0)}</text>`;}
 out+=`<line x1="50" x2="780" y1="${y(0)}" y2="${y(0)}" stroke="#bd6652" stroke-dasharray="5 5"/><line x1="${x(chosen)}" x2="${x(chosen)}" y1="20" y2="248" stroke="#6aab87" stroke-dasharray="3 4"/>`;
 out+=`<path d="${path(actual)}" stroke="#183a3c" stroke-width="2.4" fill="none"/><path d="${path(predicted)}" stroke="#768db1" stroke-width="2.4" fill="none"/><circle cx="${x(chosen)}" cy="${y(actual[chosen])}" r="5" fill="#24766a" stroke="white" stroke-width="2"/>`;
 [0,8,16,24,32,40].forEach(i=>out+=`<text x="${x(i)}" y="270" text-anchor="middle">${labels[i]}</text>`);
 $('price-chart').innerHTML=out+'<text x="50" y="12">Spot block mean · EUR/MWh</text>';
}
function reliability(bins){
 const x=v=>42+365*v,y=v=>235-210*v;let out=`<line x1="42" y1="235" x2="407" y2="25" stroke="#9db5a8" stroke-dasharray="5 4"/>`;
 for(let i=0;i<=4;i++){const v=i/4;out+=`<line x1="42" x2="407" y1="${y(v)}" y2="${y(v)}" stroke="#e4eae5"/><text x="33" y="${y(v)+4}" text-anchor="end">${v}</text><text x="${x(v)}" y="255" text-anchor="middle">${v}</text>`;}
 for(const b of bins)if(b.n)out+=`<circle cx="${x(b.predicted)}" cy="${y(b.observed)}" r="${3+Math.sqrt(b.n)/7}" fill="#24766a" opacity=".65"><title>${b.n} windows; predicted ${pct(b.predicted)}, observed ${pct(b.observed)}</title></circle>`;
 $('reliability').innerHTML=out+'<text x="42" y="13">Observed event frequency ↑</text><text x="225" y="274" text-anchor="middle">Predicted probability →</text>';
}
async function main(){
 const response=await fetch('reports/benchmark/results.json');if(!response.ok)throw Error('Report unavailable: '+response.status);const R=await response.json();$('status').textContent='';
 $('day').innerHTML=R.areas.DK1.days.filter(d=>d.split==='test').map(d=>`<option>${d.date}</option>`).join('');
 function render(){
  const area=$('area').value,r=R.areas[area],days=r.days.filter(d=>d.split==='test'),d=days.find(d=>d.date===$('day').value),policy=$('policy').value,mw=Number($('mw').value),charge=Number($('charge').value),i=d.choices[policy],reg=r.selected.regression,prob=r.selected.probability,summary=totals(days,policy,mw,charge),selected=r.test.policies[policy];
  const actual=cost(d.actual[i],mw,charge),saving=cost(d.actual[16],mw,charge)-actual,regret=actual-cost(Math.min(...d.actual),mw,charge),p=d.probability[prob][i];
  $('issue').textContent=`Issued ${new Date(d.issue).toLocaleString('en-GB',{timeZone:'Europe/Copenhagen'})} Europe/Copenhagen · 41 feasible starts · eight quarters per job`;
  $('selection').textContent=`June-selected families: ${modelNames[reg]} for cost scheduling; ${modelNames[prob]} for negative-block probabilities. ${policy==='oracle'?'Perfect hindsight uses future actual prices and is shown only as a lower bound.':'The inspected schedule uses information available at the modeled commitment time.'}`;
  plot(d.actual,d.regression[reg],i,d.labels);$('policy-label').textContent=names[policy];$('window').textContent=d.labels[i]+'–'+endTime(d.labels[i]);$('run-time').textContent=fmt(2*mw,1)+' MWh · '+fmt(mw,1)+' MW';
  $('timeline').innerHTML=Array.from({length:48},(_,j)=>`<i class="${j>=i&&j<i+8?'on':''}"></i>`).join('');$('timeline').setAttribute('aria-label',`Run from ${d.labels[i]} to ${endTime(d.labels[i])}, ${2*mw} MWh`);
  $('daily-cost').textContent=euros(actual);$('daily-saving').textContent=euros(Math.abs(saving))+(saving>=0?' saved':' extra cost');$('daily-regret').textContent=euros(regret);$('prob-value').textContent=pct(p);$('prob-fill').style.width=(p*100)+'%';$('event-result').textContent=`Observed spot block: ${d.actual[i]<0?'negative':'not negative'} (${fmt(d.actual[i])} €/MWh).`;
  $('mw-label').textContent=fmt(mw,1)+' MW';$('charge-label').textContent='€'+fmt(charge,0)+' / MWh';$('period-note').textContent=`${area} · 92 daily jobs · ${fmt(summary.energy,0)} MWh · ${names[policy]}`;
  $('stats').innerHTML=stat('Savings versus noon',euros(summary.savings),'Whole replay · selected scenario')+stat('Actual job cost',euros(summary.total),'92 jobs · includes scenario charge')+stat('Cheaper days',summary.cheaper+' / 92',summary.dearer+' days cost more than noon')+stat('Hindsight regret',euros(summary.regret),'Gap to the unattainable perfect schedule');
  $('finding').textContent=`${names[policy]} ${summary.savings>=0?'saved':'cost an extra'} ${euros(Math.abs(summary.savings))} versus fixed noon. Its largest daily overspend was ${euros(summary.worst)}. ${summary.negative} of 92 jobs had a negative ${charge?'charge-adjusted':'spot-only'} cost. These are replay results, not a bill-saving guarantee.`;
  $('policy-table').innerHTML=policies.map(k=>{const s=totals(days,k,mw,charge);return `<tr class="${k===policy?'selected':''}"><td>${names[k]}</td><td>${fmt(s.total)}</td><td>${fmt(s.savings)}</td><td>${fmt(s.regret)}</td><td>${s.cheaper} / ${s.dearer}</td><td>${s.negative} / 92</td></tr>`;}).join('');
  $('calendar').innerHTML=days.map(x=>{const s=cost(x.actual[16],mw,charge)-cost(x.actual[x.choices[policy]],mw,charge);return `<button class="${s>1e-9?'gain':s< -1e-9?'loss':''} ${x.date===d.date?'active':''}" data-date="${x.date}" aria-label="${x.date}, savings ${fmt(s)} euros" title="${x.date}: ${euros(s)} savings">${x.date.slice(8)}/${Number(x.date.slice(5,7))}</button>`;}).join('');
  $('model-table').innerHTML=Object.entries(r.test.regression).map(([k,v])=>`<tr class="${k===reg?'selected':''}"><td>${modelNames[k]}${k===reg?' · chosen':''}</td><td>${fmt(r.validation.regression[k].scheduling_cost)}</td><td>${fmt(v.scheduling_cost)}</td><td>${fmt(v.mae)}</td></tr>`).join('');
  $('prob-table').innerHTML=Object.entries(r.test.probability).map(([k,v])=>`<tr class="${k===prob?'selected':''}"><td>${modelNames[k]}${k===prob?' · chosen':''}</td><td>${fmt(v.brier,4)}</td><td>${fmt(v.roc_auc,3)}</td><td>${pct(v.base_rate)}</td></tr>`).join('');reliability(r.test.probability[prob].reliability);
  const b=selected.daily_savings_interval;$('bootstrap').textContent=`${names[policy]}: mean daily savings ${euros(b.mean*mw)}, descriptive 95% daily bootstrap interval [${euros(b.lower*mw)}, ${euros(b.upper*mw)}]. Resamples whole days; does not capture dependence beyond a day. Uniform charges cancel from savings.`;
 }
 ['area','day','policy'].forEach(id=>$(id).addEventListener('change',render));['mw','charge'].forEach(id=>$(id).addEventListener('input',render));
 $('calendar').addEventListener('click',e=>{const button=e.target.closest('button[data-date]');if(button){$('day').value=button.dataset.date;render();$('planner').scrollIntoView({behavior:'smooth'});}});
 $('download').addEventListener('click',()=>{const area=$('area').value,r=R.areas[area],d=r.days.find(d=>d.date===$('day').value),url=URL.createObjectURL(new Blob([dailyCSV(area,d,r.selected,$('policy').value,Number($('mw').value),Number($('charge').value))],{type:'text/csv'})),a=document.createElement('a');a.href=url;a.download=`lowtide-${area}-${d.date}.csv`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});render();
}
main().catch(e=>{$('status').textContent='Unable to load replay: '+e.message;});

