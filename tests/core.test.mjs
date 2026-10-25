import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {cost,totals,select,dailyCSV,policies} from '../web/core.mjs';
const R=JSON.parse(fs.readFileSync(new URL('../reports/benchmark/results.json',import.meta.url)));
test('all browser decisions match Python, including probability tie breaks',()=>{
 for(const r of Object.values(R.areas))for(const d of r.days)assert.deepEqual(select(d.regression[r.selected.regression],d.probability[r.selected.probability],d.actual,d.regression.profile,d.regression.weekly),d.choices);
});
test('browser totals match every policy and area',()=>{
 for(const r of Object.values(R.areas))for(const p of policies){const s=totals(r.days.filter(d=>d.split==='test'),p),e=r.test.policies[p];assert.ok(Math.abs(s.total-e.total_cost)<1e-8);assert.ok(Math.abs(s.savings-e.savings)<1e-8);assert.ok(Math.abs(s.regret-e.regret)<1e-8);assert.equal(s.negative,e.negative_jobs);assert.equal(s.dearer,e.dearer_days);assert.equal(s.cheaper,e.cheaper_days);}
});
test('uniform charge changes cost but not savings or regrets',()=>{
 const ds=R.areas.DK1.days.filter(d=>d.split==='test');const a=totals(ds,'cost',2,0),b=totals(ds,'cost',2,50);
 assert.ok(Math.abs(b.total-a.total-92*4*50)<1e-8);assert.ok(Math.abs(b.savings-a.savings)<1e-8);assert.ok(Math.abs(b.regret-a.regret)<1e-8);assert.ok(b.negative<=a.negative);
});
test('cost units and invalid scenario boundaries',()=>{assert.equal(cost(-20,1,30),20);assert.equal(cost(30,2,10),160);assert.throws(()=>cost(1,0,0));assert.throws(()=>cost(1,1,101));assert.throws(()=>select([],[],[],[],[]));});
test('daily export contains scenario, family identity and exactly one chosen block',()=>{
 const r=R.areas.DK2,d=r.days.find(d=>d.split==='test');const rows=dailyCSV('DK2',d,r.selected,'negative',2,50).trim().split('\r\n'),header=rows.shift().split(','),records=rows.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[header[i],v])));
 assert.equal(records.length,41);assert.equal(records.filter(r=>r.chosen==='1').length,1);
 const chosen=records.find(r=>r.chosen==='1'),i=d.choices.negative;assert.equal(chosen.start_utc,d.starts[i]);assert.equal(chosen.selected_probability,r.selected.probability);assert.equal(chosen.selected_regression,r.selected.regression);assert.equal(Number(chosen.scenario_cost_eur),cost(d.actual[i],2,50));
});
test('future actuals cannot alter deployable policy choices',()=>{
 const r=R.areas.DK1,d=r.days[0],p=d.regression[r.selected.regression],prob=d.probability[r.selected.probability],a=select(p,prob,d.actual,d.regression.profile,d.regression.weekly),b=select(p,prob,d.actual.map(x=>-x),d.regression.profile,d.regression.weekly);
 for(const k of policies.filter(k=>k!=='oracle'))assert.equal(a[k],b[k]);
});
