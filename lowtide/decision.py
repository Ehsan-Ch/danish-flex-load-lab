"""Pure schedule selection and dimensional cost accounting."""
import math
import numpy as np

POLICIES = ('fixed','profile','weekly','cost','negative','oracle')

def choose(predicted, probabilities, actual, profile, weekly):
    arrays = [np.asarray(x,float) for x in (predicted,probabilities,actual,profile,weekly)]
    if any(x.shape != (41,) or not np.isfinite(x).all() for x in arrays):
        raise ValueError('A complete 41-window day is required')
    p, prob, a, base, week = arrays
    if ((prob<0)|(prob>1)).any():
        raise ValueError('Invalid probabilities')
    return {'fixed':16,'profile':int(np.argmin(base)),'weekly':int(np.argmin(week)),
            'cost':int(np.argmin(p)),
            'negative':min(range(41),key=lambda i:(-prob[i],p[i],i)),
            'oracle':int(np.argmin(a))}

def cost(mean_price, mw=1., charge=0.):
    if not all(math.isfinite(x) for x in (mean_price,mw,charge)) or not .5<=mw<=5 or not 0<=charge<=100:
        raise ValueError('Invalid cost scenario')
    return 2*mw*(mean_price+charge)

def bootstrap(savings):
    v = np.asarray(savings,float)
    if v.ndim != 1 or not len(v) or not np.isfinite(v).all():
        raise ValueError('Invalid daily savings')
    draws = np.random.default_rng(42).choice(v,size=(2000,len(v)),replace=True).mean(axis=1)
    return {'mean':float(v.mean()),'lower':float(np.quantile(draws,.025)),
            'upper':float(np.quantile(draws,.975)),'days':len(v),'unit':'EUR per daily 1 MW job'}

def summarize(days, policy):
    values = np.array([cost(d['actual'][d['choices'][policy]]) for d in days])
    fixed = np.array([cost(d['actual'][d['choices']['fixed']]) for d in days])
    oracle = np.array([cost(min(d['actual'])) for d in days])
    savings = fixed-values
    return {'days':len(days),'energy_mwh':2*len(days),'total_cost':float(values.sum()),
            'mean_cost':float(values.mean()),'savings':float(savings.sum()),
            'regret':float((values-oracle).sum()),'negative_jobs':int((values<0).sum()),
            'cheaper_days':int((savings>1e-9).sum()),'dearer_days':int((savings < -1e-9).sum()),
            'maximum_daily_overspend':float(max(0,-savings.min())),
            'daily_savings_interval':bootstrap(savings)}
