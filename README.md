# Lowtide · Danish Flexible Load Lab

[Live scheduling lab](https://ehsan-ch.github.io/danish-flex-load-lab/) · [Fixed protocol](docs/PROTOCOL.md) · [Model card](docs/MODEL_CARD.md) · [Verification](docs/VALIDATION.md)

**Same energy. Better timing?** Lowtide tests whether forecasts can choose a cheaper two-hour electricity-use window in Denmark. It combines negative spot-cost probability estimation with a constrained scheduling replay, comparing realized decisions rather than only prediction errors.

![Lowtide scheduling preview](reports/preview.jpg)

## The decision

A mandatory constant load must run for eight uninterrupted 15-minute intervals inside 08:00–20:00 local time. There are **41 feasible starts**, from 08:00 to 18:00. Every policy delivers 2 MWh at the default 1 MW capacity. The schedule is committed at **10:00 Copenhagen on D−1**. Fixed noon (12:00–14:00) is the reference.

This early commitment is central: if the consumer can wait for the published auction prices and has no further uncertainty, it can solve this simplified day-ahead problem directly without forecasting. Lowtide is a historical research experiment, not a live plant controller, a retail tariff calculator or an execution system.

## Recorded result

June validation selected the **recent per-start-time price profile** for cost scheduling in both areas. Families were then locked for the 92-day July–September replay, with monthly refits. At 1 MW, spot-only:

| Area | Fixed-noon cost | Selected cost | Savings vs noon | Cheaper / dearer days | Gap to perfect hindsight |
|---|---:|---:|---:|---:|---:|
| DK1 | €7,659.13 | €7,126.97 | **€532.16** | 64 / 28 | €381.30 |
| DK2 | €8,329.06 | €7,849.11 | **€479.94** | 68 / 24 | €384.73 |

Daily mean savings: DK1 €5.78 with descriptive 95% daily-bootstrap interval [€3.24, €8.51]; DK2 €5.22 [€3.11, €7.46]. Resampling days preserves within-day dependence but ignores longer dependence. These are not guaranteed future bill savings.

The result illustrates why **maximizing the probability of a negative-price block is different from minimizing cost**. The negative-first policy saved €476.21 in DK1 but only €95.96 in DK2. In DK2 it overspent noon by as much as €172.63 on one day, and its mean-savings interval included zero. Weekly-lag scheduling cost slightly more than fixed noon overall in both areas.

Boosting had lower replay price MAE than the selected profile in both areas, yet its schedules cost more. A better average price forecast did not yield a better timing decision. Probability selection also did not transfer cleanly: June selected the profile in DK1 and logistic in DK2; later Brier scores favored logistic in DK1 and boosting in DK2. We retain the original selections and show all results. A calibration method and a good validation score do not guarantee future calibration or good scheduling decisions.

## Explore

The [public preview](https://ehsan-ch.github.io/danish-flex-load-lab/) runs entirely in the browser without an API key. Choose DK1/DK2, a delivery day and a policy. Inspect predicted versus actual block prices, the committed run, negative spot-cost probability, daily savings and the full-period comparison. Click a day in the savings calendar to inspect successes and failures.

Two scenario sliders change load power (0.5–5 MW) and a **hypothetical uniform extra charge** (0–100 EUR/MWh). Equal energy means a uniform charge changes all costs equally but cannot change schedule rankings, savings or regret. It can eliminate negative total costs. Probabilities still refer to spot-only block means. The charge is not an estimate of any Danish network tariff, supplier fee, VAT or tax.

## Run locally

Python 3.11 or 3.12; Node 22 for browser-math tests:

```sh
python -m venv .venv
# Activate .venv using your shell's normal command.
python -m pip install -e .
python -m lowtide.cli serve
# Open http://127.0.0.1:8791/
python -m unittest discover -s tests -v
node --test tests/core.test.mjs
```

The frozen preview and tests do not need fresh API data. To rebuild the experiment:

```sh
python -m lowtide.cli download --cache data
python -m lowtide.cli run --cache data --output reports/custom
```

Use a fresh cache directory for a new download; existing provenance is never silently overwritten. CPU training takes a few minutes, with no paid API or GPU. The preview deliberately reads `reports/benchmark`, not custom runs. Compare results before intentionally replacing that release. Package versions are pinned; later API revisions can change source hashes and fitted results. Exact original training requires the original verified raw cache, which is not committed. The published predictions and quarter prices suffice to audit scheduling decisions and realized costs.

## Method

- **Data:** 70,080 official Energinet native-quarter records, DK1/DK2, 1 October 2025 inclusive to 1 October 2026 exclusive in Danish local time. Negative prices retained; gaps, duplicates and nonfinite values rejected.
- **Features:** 34 block/calendar features using 72/96/168/336-hour elapsed lags, other-area block means, lagged daily statistics and known calendar values. Every historical price is assumed available 24 hours after its interval ends. Minimum feature-availability margin in the source is 13 hours.
- **Splits:** 120 fit days plus 28 separate calibration days, monthly updates. Validation 1–27 June; replay 1 July–30 September. Later monthly updates may consume earlier replay labels once matured.
- **Selection:** choose the regression family by realized validation scheduling cost; choose the probability family by validation Brier. Candidate regressors: weekly lag, recent profile, ridge and histogram boosting. Candidate probabilities: recent profile, logistic plus isotonic, boosting plus isotonic.
- **Targets:** mean price across each candidate's eight quarters, and whether that mean is strictly below zero. Some quarters can be positive inside a negative-mean block.
- **Policies:** fixed noon, recent profile, weekly lag, selected cost forecast, negative-first and perfect hindsight. Ties are deterministic. Hindsight sees future actuals and is labeled as an unattainable lower bound.

The protocol was written before running this comparison, but this same market period was previously examined in other projects. It is a **familiar retrospective benchmark**, not an independent prospective holdout. Overlapping windows are dependent. No weather/load forecasts, plant constraints, network tariffs or market impact are modeled. See the [model card](docs/MODEL_CARD.md).

## Audit artifacts

| File | Contents |
|---|---|
| `reports/benchmark/results.json` | Both areas, all full-precision predictions, quarter prices, selections, split boundaries, metrics, provenance and protocol hash |
| `reports/benchmark/windows.csv.gz` | 9,758 validation-plus-replay candidate rows; 7,544 belong to the replay |
| `reports/benchmark/schedule-journal.csv` | 1,428 policy decisions with issue/start times, energy, cost, savings, regret and chosen model identities |
| Browser daily CSV | All 41 candidates with selected model identities, inspected policy and current scenario parameters |

`lowtide/` contains the research pipeline, `web/` the static interface, and `tests/` the time, leakage, scheduling and reconciliation checks. GitHub Actions checks Python 3.11/3.12 and Node 22. There are no external scripts, fonts, analytics, stored credentials or browser uploads.

Original code/documentation: MIT. Energinet source and adapted data-derived reports: CC BY 4.0. See [ATTRIBUTION.md](ATTRIBUTION.md). The verified data adapter/cache methodology is reused from the author's Nordcast and Beltline projects; the block targets, scheduling policies, decision-focused selection, replay and interface are new.
