# Verification record

25 October 2026. Completed the fixed monthly experiment using the SHA-256-verified cache and predeclared protocol. All eight area/month model fits completed. The published artifacts retain 9,758 candidate windows and 1,428 policy decisions, including validation.

Local checks: **24 Python tests and 6 Node tests passed**. They check source gaps/duplicates/nonfinite values, negative prices, DST days and feasible job lengths, label and feature readiness, future-data mutation, deterministic ties, non-oracle independence from future actual prices, cost units/scaling/uniform charges, probability endpoints/undefined metrics, constant-class calibration, protocol hash, model selection, all window means against retained source quarters, decision journals, aggregate metrics and browser/Python reconciliation. Server checks confirm private cache and traversal paths are not exposed.

Local browser checks: DK2, 30 September, negative-first, 2 MW and a hypothetical €50/MWh charge selected 12:45–14:45, cost €288.91, savings €27.68 and regret €1.64. The downloaded CSV had 41 candidates, exactly one chosen row, the correct model identities/scenario and the matching full-precision cost. Calendar navigation changed the inspected day; hindsight selection displayed its future-information warning. Mobile testing at 390×844 exposed a grid minimum-width issue, which was corrected; document content width and scroll width both measured 375 pixels afterward. Desktop charts and controls were inspected as well.

Code/data release: `7405b021aba1eb2299fe428ad02bdef063242801`. All 30 published file hashes matched the staged Git manifest. Local checkout was synchronized to the release with a clean working tree.

[GitHub Tests run 40183564707](https://github.com/Ehsan-Ch/danish-flex-load-lab/actions/runs/40183564707): **success**, including Python 3.11, Python 3.12 and Node 22 browser-math jobs. [Pages deployment run 40183569917](https://github.com/Ehsan-Ch/danish-flex-load-lab/actions/runs/40183569917): **success**.

The [public preview](https://ehsan-ch.github.io/danish-flex-load-lab/) loaded the report and rendered the interactive scheduling interface. On the hosted page, switching to DK2 / 30 September / negative-first selected 12:45–14:45 and showed whole-replay savings of €95.96 at 1 MW, matching the frozen report. The hosted schedule journal was downloaded and its bytes matched the published Git artifact exactly. The final documentation-only update leaves the tested code and data unchanged.
