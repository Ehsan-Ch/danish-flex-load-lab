# Lowtide model and decision card

## Intended use

Research and portfolio demonstration of constrained load scheduling in Danish electricity markets. Not a production automation system, an investment recommendation or a retail-bill guarantee. No hardware, broker or electricity-provider account is connected.

## Modeled decision

One mandatory two-hour constant-power job per day and area, with 41 feasible quarter-aligned starts from 08:00 through 18:00. Commitment is at 10:00 Copenhagen on the previous day, without later rescheduling. Fixed reference is noon. Each candidate delivers equal energy, and no operating costs differ other than its electricity price. This excludes production dependencies, heat/charge dynamics, efficiency differences, ramp limits, restart penalties and uncertain job completion.

Cost = MW × 0.25 hours × sum of eight quarter prices = MW × 2 hours × block mean. The event probability estimates **mean spot price < 0**, not every price < 0 and not a negative all-in bill. Uniform user charges apply to all energy and therefore cancel from savings comparisons; actual time-varying tariffs could alter the ranking.

## Data and temporal validity

Official Energinet DayAheadPrices: 70,080 records, October 2025 through September 2026. UTC keys are unique and Danish delivery days contain 92, 96 or 100 quarters. Jobs are deliberately limited to daytime and remain two elapsed hours on DST transition days. Source cache and metadata are SHA-256 checked. Negative prices are retained.

Price availability is assumed at interval end +24 hours. Feature timestamps include the *last* quarter of each lagged block. The minimum margin before issue time is 13 hours. Historical archive revisions cannot be reconstructed; no claim of point-in-time publication-vintage accuracy is made. This period was already inspected in earlier research, so benchmark familiarity is explicitly disclosed.

## Models

34 features: own block mean/min/max/negative-quarter share at four elapsed-hour lags (16), other-zone block means (4), 96-quarter lagged mean/std (2), daily/annual harmonics (4), weekday one-hot (7) and local UTC offset (1). No future weather, demand, generation or network inputs.

Each area has separate ridge and histogram-boosting regression, plus weekly-lag and recent per-start-time profile baselines. Classifiers are logistic and histogram boosting with separate isotonic calibration; the probability baseline is Laplace-smoothed per-start-time frequency. Exact fixed parameters are in [PROTOCOL.md](PROTOCOL.md). A constant-class fallback handles calibration after a one-class fitting window. Empty reliability bins and undefined discrimination metrics use null, not invented zeros.

## Fitting and evaluation

Monthly refits use 120 fitting days then 28 calibration days, ending before the monthly first issue. June 1–27 chooses cost models by realized scheduling cost and probability models by Brier. Families stay fixed through July–September; parameters/calibrators update monthly with matured labels. The recent profile directly uses calibration prices as its fitting history and therefore is a baseline trained on that more recent block, not a model fitted on the earlier 120-day block. This difference is intentional and disclosed.

Candidate-window accuracy and reliability statistics describe overlapping windows, not 3,772 independent trials per area. The primary decision evaluation uses 92 daily jobs. Paired bootstrap intervals resample full days 2,000 times with seed42; dependence beyond a day and model-selection uncertainty are not captured.

## Results and failures

Both areas selected the recent-price profile for cost. At 1 MW it saved €532.16 in DK1 and €479.94 in DK2 versus fixed noon over 92 days, but was more expensive on 28 and 24 days respectively. The remaining gap to hindsight was €381.30 and €384.73. The costs exclude actual tariffs and fees.

Negative-first scheduling does not optimize expected cost. DK2's negative-first policy saved only €95.96, with a €172.63 maximum daily overspend. Its mean-savings bootstrap interval crossed zero. Classification success and operational savings are distinct metrics.

June probability selection failed to transfer to the best replay Brier family in either area. DK1 selected profile (replay Brier .06709), while logistic was better (.05887). DK2 selected logistic (.02153), while boosting was better (.01344). Those outcomes do not trigger retrospective reselection. The selected DK2 model can have useful ranking but poor probability calibration; neither isotonic fitting nor ROC AUC establishes operational value.

## Reproducibility and next research

Frozen artifacts retain issue times, window prices, model predictions, decisions, costs and hashes. All policy costs reconcile to source quarters, and JavaScript calculations are checked against Python. Exact retraining needs the original cache because the live archive may change.

A follow-up experiment should freeze a genuinely new prospective period, timestamp exogenous forecasts, and include a specific load's real constraints and time-varying tariff contract. It should compare against a strong recent-profile baseline and distinguish early commitment from scheduling after auction publication. Do not retune against this same replay and call the dates a new independent test.
