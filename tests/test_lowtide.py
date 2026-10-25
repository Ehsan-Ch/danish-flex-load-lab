import csv
import gzip
import json
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path
import numpy as np
from lowtide.data import day_slots, decision, available, validate, stamp, parse, midnight, STEP, DK, digest
from lowtide.windows import candidates, matrix, NAMES
from lowtide.models import Models, probability_metrics
from lowtide.decision import choose, cost, summarize, bootstrap, POLICIES
from lowtide.pipeline import bounds
from lowtide.server import Handler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT/'reports/benchmark/results.json').read_text())

class DataAndTime(unittest.TestCase):
    def test_dst_day_lengths(self):
        self.assertEqual(len(day_slots('2025-10-26')),100)
        self.assertEqual(len(day_slots('2026-03-29')),92)
        self.assertEqual(len(set(day_slots('2025-10-26'))),100)

    def test_feasible_windows_across_dst(self):
        for day in ('2025-10-26','2026-03-29','2026-07-01'):
            blocks = candidates(day)
            self.assertEqual(len(blocks),41)
            self.assertEqual(blocks[0][0].astimezone(DK).hour,8)
            self.assertEqual((blocks[-1][-1]+STEP).astimezone(DK).hour,20)
            self.assertTrue(all(len(b)==8 and b[-1]+STEP-b[0]==timedelta(hours=2) for b in blocks))

    def test_issue_clock_and_calibration_cutoff(self):
        self.assertEqual(decision('2026-07-01').hour,8)
        self.assertEqual(decision('2026-01-01').hour,9)
        for month in (6,7,8,9):
            first = date(2026,month,1)
            a,b,c = bounds(first)
            self.assertEqual((b-a).days,120)
            self.assertEqual((c-b).days,28)
            self.assertLess(available(candidates(c-timedelta(days=1))[-1][-1]),decision(first))

    def records(self):
        return [{'TimeUTC':stamp(t),'PriceArea':a,'DayAheadPriceEUR':-5.} for t in day_slots('2026-07-01') for a in ('DK1','DK2')]

    def test_preserve_negative_price(self):
        v = validate(self.records(),'2026-07-01','2026-07-02')
        self.assertEqual(min(v['DK1'].values()),-5)

    def test_gap_and_duplicate_rejection(self):
        r = self.records()
        for bad in (r[:-1],r+[r[0]]):
            with self.assertRaises(ValueError):
                validate(bad,'2026-07-01','2026-07-02')

    def test_nonfinite_misaligned_rejection(self):
        for k,v in [('DayAheadPriceEUR',float('nan')),('TimeUTC','2026-06-30T22:01:00Z')]:
            r = self.records();r[0][k] = v
            with self.assertRaises(ValueError):
                validate(r,'2026-07-01','2026-07-02')

    def test_feature_future_mutation(self):
        ts = [midnight('2026-01-01')+i*STEP for i in range(18*96)]
        source = {a:{t:float(i%96+shift) for i,t in enumerate(ts)} for a,shift in [('DK1',-30),('DK2',10)]}
        a = matrix(source,'DK1')
        day = date(2026,1,17)
        ids = [i for i,d in enumerate(a['days']) if d==day]
        for area in source:
            for t in ts:
                if available(t)>decision(day):
                    source[area][t] += 10000
        b = matrix(source,'DK1')
        np.testing.assert_array_equal(a['X'][ids],b['X'][ids])
        self.assertFalse(np.array_equal(a['y'][ids],b['y'][ids]))
        self.assertEqual(a['X'].shape[1],len(NAMES))
        self.assertEqual(len(ids),41)

class Decisions(unittest.TestCase):
    def test_tie_breaking_and_known_noon_index(self):
        c = choose([0]*41,[.1]*41,[1]*41,[2]*41,[3]*41)
        self.assertEqual(c['fixed'],16)
        self.assertTrue(all(c[k]==0 for k in POLICIES if k!='fixed'))

    def test_probability_then_cost_then_earliest(self):
        p = [.1]*41;p[8]=p[9]=p[10]=.9
        f = [0]*41;f[9]=f[10]=-2
        self.assertEqual(choose(f,p,[1]*41,[1]*41,[1]*41)['negative'],9)

    def test_nonoracle_choices_ignore_future_outcomes(self):
        f = np.arange(41).tolist();p=[.5]*41
        a = choose(f,p,f,f,f)
        b = choose(f,p,[-x for x in f],f,f)
        for k in POLICIES:
            if k!='oracle':
                self.assertEqual(a[k],b[k])
        self.assertNotEqual(a['oracle'],b['oracle'])

    def test_energy_units_charge_and_scaling(self):
        self.assertEqual(cost(30,2,10),160)
        self.assertEqual(cost(-20,1,30),20)
        self.assertEqual(cost(20,1,0)-cost(10,1,0),cost(20,1,100)-cost(10,1,100))

    def test_invalid_scenarios_and_candidates(self):
        for mw,charge in ((0,0),(6,0),(1,-1),(1,101),(float('nan'),0)):
            with self.assertRaises(ValueError):cost(1,mw,charge)
        with self.assertRaises(ValueError):choose([0]*40,[0]*41,[0]*41,[0]*41,[0]*41)
        with self.assertRaises(ValueError):choose([0]*41,[1.1]*41,[0]*41,[0]*41,[0]*41)

    def test_bootstrap_deterministic(self):
        self.assertEqual(bootstrap([1,2,3]),bootstrap([1,2,3]))
        self.assertEqual(bootstrap([2]*92)['lower'],2)

class Probabilities(unittest.TestCase):
    def test_reliability_endpoints(self):
        r = probability_metrics([0,1],[0,1])
        self.assertEqual(r['brier'],0)
        self.assertEqual(r['reliability'][0]['n'],1)
        self.assertEqual(r['reliability'][9]['n'],1)
        self.assertIsNone(r['reliability'][5]['observed'])

    def test_undefined_auc_and_bad_labels(self):
        self.assertIsNone(probability_metrics([0,0],[.1,.2])['roc_auc'])
        self.assertIsNone(probability_metrics([1,1],[.1,.2])['average_precision'])
        with self.assertRaises(ValueError):probability_metrics([.5],[.5])

    def test_constant_class_and_calibration_not_refit(self):
        rng = np.random.default_rng(42);X = rng.normal(size=(282,3))
        model = Models().fit(X[:200],np.ones(200))
        coef = model.reg['ridge'].named_steps['ridge'].coef_.copy()
        model.calibrate(X[200:],-np.ones(82),np.tile(np.arange(41),2))
        reg,prob = model.predict(X[:41],np.zeros(41),np.arange(41))
        np.testing.assert_array_equal(coef,model.reg['ridge'].named_steps['ridge'].coef_)
        np.testing.assert_array_equal(prob['boosted'],np.ones(41))
        np.testing.assert_array_equal(prob['profile'],np.full(41,.75))
        np.testing.assert_array_equal(reg['profile'],-np.ones(41))

class Evidence(unittest.TestCase):
    def test_protocol_hash(self):
        self.assertEqual(R['protocol_sha256'],digest((ROOT/'docs/PROTOCOL.md').read_bytes()))

    def test_selection_and_dates(self):
        for report in R['areas'].values():
            self.assertEqual(report['selected']['regression'],min(report['validation']['regression'],key=lambda k:report['validation']['regression'][k]['scheduling_cost']))
            self.assertEqual(report['selected']['probability'],min(report['validation']['probability'],key=lambda k:report['validation']['probability'][k]['brier']))
            days = [d for d in report['days'] if d['split']=='test']
            self.assertEqual(len(days),92)
            self.assertEqual(sum(len(d['actual']) for d in days),3772)
            self.assertEqual(days[0]['date'],'2026-07-01')
            self.assertEqual(days[-1]['date'],'2026-09-30')

    def test_source_quarters_reconcile_every_window(self):
        for report in R['areas'].values():
            for d in report['days']:
                prices = dict(zip(d['quarter_times'],d['quarter_prices']))
                self.assertEqual(d['issue'],stamp(decision(d['date'])))
                for i,block in enumerate(candidates(d['date'])):
                    self.assertEqual(d['starts'][i],stamp(block[0]))
                    self.assertAlmostEqual(d['actual'][i],sum(prices[stamp(t)] for t in block)/8)

    def test_every_decision_and_regret(self):
        for r in R['areas'].values():
            for d in r['days']:
                c = choose(d['regression'][r['selected']['regression']],d['probability'][r['selected']['probability']],d['actual'],d['regression']['profile'],d['regression']['weekly'])
                self.assertEqual(d['choices'],c)
                for i in c.values():self.assertGreaterEqual(d['actual'][i]-min(d['actual']),-1e-12)

    def test_aggregate_and_probabilities_reconcile(self):
        for r in R['areas'].values():
            days = [d for d in r['days'] if d['split']=='test']
            for p in POLICIES:self.assertEqual(summarize(days,p),r['test']['policies'][p])
            y = np.concatenate([d['actual'] for d in days])<0
            for k in ('profile','logistic','boosted'):
                p = np.concatenate([d['probability'][k] for d in days])
                self.assertEqual(probability_metrics(y,p),r['test']['probability'][k])

    def test_compressed_candidate_export(self):
        with gzip.open(ROOT/'reports/benchmark/windows.csv.gz','rt') as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),2*119*41)
        self.assertEqual(len({(r['area'],r['start_utc']) for r in rows}),len(rows))
        self.assertEqual(sum(r['split']=='test' for r in rows),2*92*41)
        for r in rows:
            report = R['areas'][r['area']]
            d = next(d for d in report['days'] if d['date']==r['delivery_day'])
            i = d['starts'].index(r['start_utc'])
            self.assertAlmostEqual(float(r['actual_mean_eur_mwh']),d['actual'][i])

    def test_schedule_journal_reconciles(self):
        with (ROOT/'reports/benchmark/schedule-journal.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),2*119*6)
        for area,r in R['areas'].items():
            for p in POLICIES:
                group = [x for x in rows if x['area']==area and x['split']=='test' and x['policy']==p]
                self.assertEqual(len(group),92)
                self.assertAlmostEqual(sum(float(x['spot_cost_eur']) for x in group),r['test']['policies'][p]['total_cost'])
                self.assertTrue(all(float(x['energy_mwh'])==2 for x in group))

class Server(unittest.TestCase):
    def test_private_paths_not_served(self):
        with ThreadingHTTPServer(('127.0.0.1',0),Handler) as server:
            thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            base = f'http://127.0.0.1:{server.server_port}'
            try:
                with urllib.request.urlopen(base+'/') as r:self.assertEqual(r.status,200)
                for p in ('/data/prices.json','/.git/config','/%2e%2e/README.md','/reports/'):
                    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(base+p)
                    self.assertEqual(e.exception.code,404)
            finally:
                server.shutdown();thread.join()

if __name__=='__main__':unittest.main()
