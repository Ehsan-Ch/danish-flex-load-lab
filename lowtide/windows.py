"""Build feasible contiguous jobs and enforce the pre-issue information set."""
from datetime import timedelta
import numpy as np
from .data import DK, STEP, available, decision, day_slots

LAGS = (72, 96, 168, 336)
NAMES = [f'own_{stat}_{h}h' for h in LAGS for stat in ('mean','min','max','negative_fraction')]
NAMES += [f'other_mean_{h}h' for h in LAGS]
NAMES += ['recent_mean','recent_std','hour_sin','hour_cos','year_sin','year_cos']
NAMES += [f'weekday_{i}' for i in range(7)] + ['utc_offset']

def candidates(day):
    """41 starts, each with eight consecutive quarters wholly inside 08–20."""
    slots = day_slots(day)
    result = []
    for i, t in enumerate(slots):
        block = slots[i:i+8]
        if len(block) != 8:
            continue
        start, end = t.astimezone(DK), (block[-1]+STEP).astimezone(DK)
        if start.hour >= 8 and start.hour*60+start.minute <= 18*60 and end.date() == start.date() and end.hour*60+end.minute <= 20*60:
            result.append(block)
    if len(result) != 41:
        raise ValueError('Unexpected candidate grid')
    return result

def matrix(values, area):
    other = 'DK2' if area == 'DK1' else 'DK1'
    times = sorted(values[area])
    if times != sorted(values[other]) or any(b-a != STEP for a,b in zip(times,times[1:])):
        raise ValueError('Unaligned or incomplete source')
    pos = {t:i for i,t in enumerate(times)}
    own = np.array([values[area][t] for t in times],float)
    cross = np.array([values[other][t] for t in times],float)
    if not np.isfinite(own).all() or not np.isfinite(cross).all():
        raise ValueError('Nonfinite source')
    days = sorted({t.astimezone(DK).date() for t in times})
    X, y, weekly, labels, starts, margins, quarters = [], [], [], [], [], [], []
    for day in days:
        for block in candidates(day):
            if any(t not in pos for t in block):
                continue
            i = pos[block[0]]
            if i < 336*4:
                continue
            row = []
            for h in LAGS:
                v = own[i-h*4:i-h*4+8]
                row.extend([v.mean(),v.min(),v.max(),(v<0).mean()])
            row.extend(cross[i-h*4:i-h*4+8].mean() for h in LAGS)
            recent = own[i-72*4-95:i-72*4+1]
            row.extend([recent.mean(),recent.std()])
            local = block[0].astimezone(DK)
            hour = local.hour + local.minute/60
            year = local.timetuple().tm_yday
            row.extend([np.sin(hour*2*np.pi/24),np.cos(hour*2*np.pi/24),np.sin(year*2*np.pi/365.25),np.cos(year*2*np.pi/365.25)])
            row.extend(float(local.weekday()==j) for j in range(7))
            row.append(local.utcoffset().total_seconds()/3600)
            margin = (decision(day)-available(block[-1]-timedelta(hours=72))).total_seconds()/3600
            if margin < 0:
                raise ValueError('Unavailable lag feature')
            X.append(row); y.append(own[i:i+8].mean()); weekly.append(own[i-168*4:i-168*4+8].mean())
            labels.append(day); starts.append(block[0]); margins.append(margin); quarters.append(own[i:i+8].tolist())
    return {'X':np.asarray(X),'y':np.asarray(y),'weekly':np.asarray(weekly),'days':labels,'starts':starts,'quarters':quarters,'minimum_margin_hours':min(margins)}
