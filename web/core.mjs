export const policies=['fixed','profile','weekly','cost','negative','oracle'];
export const names={fixed:'Fixed noon',profile:'Recent profile',weekly:'Weekly lag',cost:'Cost forecast',negative:'Negative-first',oracle:'Perfect hindsight'};
export function cost(mean,mw=1,charge=0){
 if(![mean,mw,charge].every(Number.isFinite)||mw<.5||mw>5||charge<0||charge>100)throw Error('Invalid cost scenario');
 return 2*mw*(mean+charge);
}
export function select(predicted,probabilities,actual,profile,weekly){
 const arrays=[predicted,probabilities,actual,profile,weekly];
 if(!arrays.every(a=>a.length===41&&a.every(Number.isFinite))||!probabilities.every(v=>v>=0&&v<=1))throw Error('Invalid candidate day');
 const argmin=a=>a.reduce((best,v,i)=>v<a[best]?i:best,0);
 const neg=Array.from({length:41},(_,i)=>i).sort((a,b)=>probabilities[b]-probabilities[a]||predicted[a]-predicted[b]||a-b)[0];
 return {fixed:16,profile:argmin(profile),weekly:argmin(weekly),cost:argmin(predicted),negative:neg,oracle:argmin(actual)};
}
export function totals(days,policy,mw=1,charge=0){
 const values=days.map(d=>cost(d.actual[d.choices[policy]],mw,charge));
 const fixed=days.map(d=>cost(d.actual[16],mw,charge));
 const savings=values.map((v,i)=>fixed[i]-v),regret=values.map((v,i)=>v-cost(Math.min(...days[i].actual),mw,charge));
 const sum=a=>a.reduce((s,v)=>s+v,0);
 return {days:days.length,energy:2*mw*days.length,total:sum(values),savings:sum(savings),regret:sum(regret),negative:values.filter(v=>v<0).length,cheaper:savings.filter(v=>v>1e-9).length,dearer:savings.filter(v=>v< -1e-9).length,worst:Math.max(0,...savings.map(v=>-v))};
}
export function dailyCSV(area,day,selection,policy,mw,charge){
 const header=['area','date','issue_utc','start_utc','start_local','selected_regression','selected_probability','actual_spot_mean_eur_mwh','forecast_spot_mean_eur_mwh','negative_spot_probability','mw','uniform_charge_eur_mwh','scenario_cost_eur','inspected_policy','chosen'];
 const rows=day.starts.map((t,i)=>[area,day.date,day.issue,t,day.labels[i],selection.regression,selection.probability,day.actual[i],day.regression[selection.regression][i],day.probability[selection.probability][i],mw,charge,cost(day.actual[i],mw,charge),policy,Number(i===day.choices[policy])]);
 return [header,...rows].map(r=>r.join(',')).join('\r\n')+'\r\n';
}
