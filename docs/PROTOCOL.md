# Lowtide: fixed experiment protocol

Defined 25 October 2026 before fitting this project's models. The data/calendar have already been inspected in Nordcast and Beltline. This is a new decision-focused comparison on a familiar historical benchmark, not an independent prospective holdout.

## Task and information

Each Danish area has one mandatory, uninterrupted two-hour load per day. Default 1 MW, hence 2 MWh. Operation must fit within 08:00–20:00 Europe/Copenhagen. Starts are quarter-hour aligned: 08:00 through 18:00 inclusive, 41 candidates. There are no ramp, restart, efficiency or production-value differences between candidates. Fixed schedule starts at 12:00. All choices are committed at 10:00 local on D−1, before the modeled delivery prices are known. Later rescheduling is excluded; if a user can wait until the auction prices are published, a forecast is unnecessary for this simplified day-ahead cost problem.

Source: verified Energinet native-quarter DayAheadPrices, DK1/DK2, 2025-10-01 inclusive through 2026-10-01 exclusive, Danish local boundaries. UTC keys distinguish DST duplicates. Every historical price is assumed available 24 hours after its interval ends. This conservative assumption is not a publication-vintage reconstruction.

Regression target: mean spot price of the eight consecutive quarters in a candidate block (EUR/MWh). Event target: that mean is strictly below zero. This is a **negative spot-cost block**, not a claim that all eight prices are negative or the final retail bill is negative.

Features per candidate: own-area block mean/min/max/negative-quarter fraction at 72, 96, 168 and 336 elapsed-hour lags; other-area block mean at those lags; own-area mean/std for the 96 quarters ending at the start of the 72-hour lag; start-of-block daily and annual sine/cosine, weekday one-hot and UTC offset. Check the availability of the latest quarter in the shortest lag block against issue time. No actual future prices, weather, demand, outages or network forecasts enter the predictors.

## Monthly fitting and selection

Fit separate models for DK1 and DK2. Monthly starts: 1 June/July/August/September 2026. Fit 120 complete local delivery days, then hold out 28 calibration days. Calibration ends at midnight two days before the first delivery day. Verify every label has matured before that month's first issue. Later monthly refits may use earlier replay outcomes after maturation.

Regression recipes: weekly-block lag; recent per-start-time profile from the 28 calibration days; standardized ridge alpha=10; histogram gradient boosting squared-error mean with 100 iterations, learning rate .05, 15 leaves, minimum leaf size 40, L2=1, early stopping disabled, seed 42. No hyperparameter search.

Probability recipes: Laplace-smoothed per-start-time event frequency from calibration days; standardized logistic C=1/max_iter=1000; histogram gradient boosting classifier with the same tree settings. The two fitted classifiers are isotonic-calibrated using the separate calibration block, with clipping outside the score range. If fitting labels have one class, use that constant score and fit the calibrator as usual. No assertion that these methods guarantee calibration.

Validation deliveries: 1–27 June. Select regression family by **lowest realized total scheduling cost** when choosing its cheapest predicted block each day; deterministic earliest-start tie breaking. Select probability family separately by lowest Brier score across candidate windows. Lock both families before July. Evaluation: 1 July–30 September (92 days, 3,772 candidate windows per area). Do not tune thresholds, features or families on evaluation results.

## Policies and reporting

- Fixed noon: always 12:00–14:00.
- Recent profile: cheapest predicted block using the calibration price profile.
- Weekly lag: cheapest predicted block using last week's block prices.
- Cost forecast: cheapest predicted block using the June-selected regression.
- Negative-first: maximize June-selected probability of negative block mean, break ties by selected predicted mean, then earliest start. This policy need not minimize expected cost.
- Perfect hindsight: cheapest realized block among the same 41 starts. A lower bound on spot cost, not a deployable strategy.

All policies deliver exactly the same energy. Cost is MW × 0.25 hours × sum of the eight prices. Report actual cost, savings against fixed noon (positive means lower cost), regret versus hindsight, days with savings/losses, negative-cost jobs and maximum daily overspend versus noon. Also report regression MAE and probability Brier/log loss/AUC/average precision with undefined values null and ten-bin reliability. Overlapping candidates are dependent; do not call 3,772 windows independent trials.

Uncertainty: descriptive paired daily bootstrap of mean savings versus fixed noon, 2,000 resamples, seed42, each area separately. Preserve within-day dependence; do not claim formal inference or account for longer temporal dependence.

## Interactive scenarios and boundaries

Dashboard default is 1 MW, replaying frozen choices. Capacity slider 0.5–5 MW scales costs and energy only. An optional uniform extra charge of 0–100 EUR/MWh is a hypothetical scenario, not a Danish tariff estimate. Because energy is fixed it adds the same cost to every schedule and does not change their ranking or savings. It can turn a negative spot cost into a positive modeled total. Event probabilities remain for the spot-only mean, not the charge-adjusted total. No VAT, actual network tariffs, supplier fees, production constraints, market impact or order execution are simulated.
