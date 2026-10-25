"""Run a predeclared monthly replay and export an auditable decision journal."""
import csv
import gzip
import io
import json
import platform
from datetime import date, timedelta
from pathlib import Path
import numpy as np
import sklearn
from .data import load, available, decision, day_slots, stamp, DK, STEP, digest
from .windows import matrix, NAMES
from .models import Models, REG, PROB, probability_metrics
from .decision import choose, summarize, POLICIES, cost

ROOT = Path(__file__).resolve().parents[1]

def bounds(first):
    end = first-timedelta(days=2)
    calibration = end-timedelta(days=28)
    return calibration-timedelta(days=120),calibration,end

def run(cache, output):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    source,manifest = load(cache)
    result = {'project':'Lowtide','version':1,'source':manifest,
              'protocol_sha256':digest((ROOT/'docs/PROTOCOL.md').read_bytes()),
              'environment':{'python':platform.python_version(),'numpy':np.__version__,'sklearn':sklearn.__version__},
              'features':NAMES,'source_rows':sum(len(v) for v in source.values()),'areas':{}}
    for area in ('DK1','DK2'):
        m = matrix(source,area)
        slots = np.array([(t.astimezone(DK).hour-8)*4+t.astimezone(DK).minute//15 for t in m['starts']])
        days,folds = [],[]
        selected = None
        for month in (6,7,8,9):
            first = date(2026,month,1)
            fit_start,cal_start,cal_end = bounds(first)
            def mask(a,b):
                return np.array([a<=d<b for d in m['days']])
            fit,cal = mask(fit_start,cal_start),mask(cal_start,cal_end)
            if fit.sum()!=120*41 or cal.sum()!=28*41:
                raise ValueError('Incomplete fit/calibration grid')
            last_available = available(m['starts'][np.flatnonzero(cal)[-1]]+7*STEP)
            if last_available>decision(first):
                raise ValueError('Unavailable calibration label')
            model = Models().fit(m['X'][fit],m['y'][fit]).calibrate(m['X'][cal],m['y'][cal],slots[cal])
            stop = date(2026,6,28) if month==6 else date(2026,month+1,1)
            take = mask(first,stop)
            ids = np.flatnonzero(take)
            reg,prob = model.predict(m['X'][take],m['weekly'][take],slots[take])
            current = []
            for day in sorted({m['days'][i] for i in ids}):
                group = np.array([m['days'][i]==day for i in ids])
                di = ids[group]
                ds = day_slots(day)
                current.append({'date':str(day),'split':'validation' if month==6 else 'test','issue':stamp(decision(day)),
                                'starts':[stamp(m['starts'][i]) for i in di],
                                'labels':[m['starts'][i].astimezone(DK).strftime('%H:%M') for i in di],
                                'actual':m['y'][di].tolist(),'regression':{k:v[group].tolist() for k,v in reg.items()},
                                'probability':{k:v[group].tolist() for k,v in prob.items()},
                                'quarter_times':[stamp(t) for t in ds],'quarter_prices':[source[area][t] for t in ds]})
            y = m['y'][take]
            reg_scores = {}
            for k in REG:
                actual_costs = [cost(d['actual'][int(np.argmin(d['regression'][k]))]) for d in current]
                reg_scores[k] = {'mae':float(np.abs(y-reg[k]).mean()),'scheduling_cost':float(sum(actual_costs)),'days':len(current)}
            prob_scores = {k:probability_metrics(y<0,prob[k]) for k in PROB}
            if month==6:
                selected = {'regression':min(REG,key=lambda k:reg_scores[k]['scheduling_cost']),
                            'probability':min(PROB,key=lambda k:prob_scores[k]['brier'])}
                validation = {'regression':reg_scores,'probability':prob_scores}
            for d in current:
                d['choices'] = choose(d['regression'][selected['regression']],d['probability'][selected['probability']],
                                      d['actual'],d['regression']['profile'],d['regression']['weekly'])
            folds.append({'first_delivery':str(first),'fit_start':str(fit_start),'fit_end_exclusive':str(cal_start),
                          'calibration_end_exclusive':str(cal_end),'fit_n':int(fit.sum()),'calibration_n':int(cal.sum()),
                          'last_label_available':stamp(last_available),'first_issue':stamp(decision(first))})
            days.extend(current)
            print(area,first,'completed',flush=True)
        test = [d for d in days if d['split']=='test']
        y = np.concatenate([d['actual'] for d in test])
        scores = {'regression':{},'probability':{},'policies':{p:summarize(test,p) for p in POLICIES}}
        for k in REG:
            p = np.concatenate([d['regression'][k] for d in test])
            scores['regression'][k] = {'mae':float(np.abs(y-p).mean()),'scheduling_cost':float(sum(cost(d['actual'][int(np.argmin(d['regression'][k]))]) for d in test)),'days':len(test)}
        for k in PROB:
            scores['probability'][k] = probability_metrics(y<0,np.concatenate([d['probability'][k] for d in test]))
        result['areas'][area] = {'selected':selected,'validation':validation,'test':scores,'folds':folds,
                                'minimum_feature_margin_hours':m['minimum_margin_hours'],'days':days}
    (output/'results.json').write_text(json.dumps(result,separators=(',',':'),allow_nan=False),encoding='utf-8')
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(['area','split','delivery_day','issue_utc','start_utc','start_local','actual_mean_eur_mwh',
                     *[f'{k}_forecast_eur_mwh' for k in REG],*[f'{k}_negative_probability' for k in PROB]])
    journal = []
    for area,report in result['areas'].items():
        for d in report['days']:
            for i,start in enumerate(d['starts']):
                writer.writerow([area,d['split'],d['date'],d['issue'],start,d['labels'][i],d['actual'][i],
                                 *[d['regression'][k][i] for k in REG],*[d['probability'][k][i] for k in PROB]])
            for p,i in d['choices'].items():
                journal.append({'area':area,'split':d['split'],'delivery_day':d['date'],'issue_utc':d['issue'],
                                'policy':p,'start_utc':d['starts'][i],'start_local':d['labels'][i],
                                'energy_mwh':2,'spot_cost_eur':cost(d['actual'][i]),
                                'savings_vs_noon_eur':cost(d['actual'][16])-cost(d['actual'][i]),
                                'regret_eur':cost(d['actual'][i])-cost(min(d['actual'])),
                                'selected_regression':report['selected']['regression'],'selected_probability':report['selected']['probability']})
    (output/'windows.csv.gz').write_bytes(gzip.compress(stream.getvalue().encode(),mtime=0))
    with (output/'schedule-journal.csv').open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=list(journal[0]))
        writer.writeheader();writer.writerows(journal)
    print(json.dumps({a:{'selected':v['selected'],'policies':v['test']['policies']} for a,v in result['areas'].items()},indent=2),flush=True)
    return result
