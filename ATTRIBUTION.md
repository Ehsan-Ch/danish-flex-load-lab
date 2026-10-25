# Attribution

Source: **Energinet / Energy Data Service, DayAheadPrices**, retrieved 24 October 2026. [Dataset](https://www.energidataservice.dk/tso-electricity/DayAheadPrices), [metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices), [terms](https://www.energidataservice.dk/terms-and-conditions), [CC BY 4.0 license](https://creativecommons.org/licenses/by/4.0/).

Changes: selected DK1/DK2 and a fixed date window, constructed lagged block features and targets, trained research models, selected hypothetical operating schedules, and produced adapted charts, metrics and downloadable reports. No endorsement by Energinet is implied. Source and data-derived reports retain CC BY 4.0; original code/documentation are MIT.

Raw source SHA-256: `93ccd57867b2eae79705659e84a4aa8f1913b3a714204ccb859316a964ef7da2`.

Metadata SHA-256: `f96149b61c23e1c85ce2023b9859fb250d178cf83445f6e488bdde2a0410a162`.

Complete retrieval URL and UTC timestamp are in the report's source manifest. The source adapter and cache convention reuse Ehsan Cheraghi's [Nordcast](https://github.com/Ehsan-Ch/danish-power-forecast-lab) and [Beltline](https://github.com/Ehsan-Ch/danish-spread-risk-lab), under their MIT code license.

Context: the [European Commission's electricity-prices explanation](https://energy.ec.europa.eu/topics/markets-and-consumers/electricity-prices_en) distinguishes wholesale energy costs from retail taxes and network charges. Lowtide uses wholesale spot energy only; the optional uniform charge is a user scenario, not a quoted real tariff.
