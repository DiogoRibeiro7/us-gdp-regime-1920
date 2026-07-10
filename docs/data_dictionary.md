# Data dictionary

## `data/processed/us_gdp_series.csv`

| Column | Meaning |
|---|---|
| `year` | Calendar year. |
| `real_gdp` | Real GDP level or real GDP proxy. For Maddison, this is GDP per capita multiplied by population. For FRED, this is annual real GDP in billions of chained 2017 dollars. |
| `gdp_growth` | Annual percentage growth in real GDP. |
| `real_gdp_per_capita` | Maddison real GDP per capita, when Maddison is used. |
| `population` | Maddison population, when Maddison is used. |
| `source` | Source identifier. Default: `maddison_2023`. |
| `log_real_gdp` | Natural logarithm of real GDP. |
| `segment_id` | Fitted growth regime identifier. |
| `segment_regime` | `above_mean` or `below_mean`, based on segment mean growth relative to the full-sample mean. |
| `segment_mean_growth` | Mean annual growth rate inside the fitted segment. |

## `data/models/trend_regression.csv`

| Column | Meaning |
|---|---|
| `intercept` | Intercept from the log real GDP trend regression. |
| `slope` | Annual slope in log real GDP. |
| `r_squared` | R-squared of the log trend regression. |
| `annualised_growth_rate` | Approximate annual trend growth rate, computed as `exp(slope) - 1`. |

## `data/models/regime_segments.csv`

| Column | Meaning |
|---|---|
| `segment_id` | Segment identifier. |
| `start_year` | First year in the regime. |
| `end_year` | Last year in the regime. |
| `n_observations` | Number of annual observations. |
| `mean_growth` | Segment mean annual real GDP growth. |
| `long_run_mean` | Full-sample mean annual real GDP growth. |
| `regime` | `above_mean` or `below_mean`. |
| `sse` | Within-segment sum of squared errors around the segment mean. |

## `data/models/fred_maddison_growth_comparison.csv`

| Column | Meaning |
|---|---|
| `year` | Calendar year in the overlapping period. |
| `growth_maddison` | Growth rate from Maddison-derived real GDP proxy. |
| `growth_fred` | Growth rate from FRED/BEA `GDPCA`. |
| `growth_difference` | Maddison growth minus FRED growth. |

## `data/models/fiscal_ratios.csv`

| Column | Meaning |
|---|---|
| `year` | Calendar year. |
| `gross_debt_gdp` | Gross federal debt as a percent of GDP. |
| `public_debt_gdp` | Federal debt held by the public as a percent of GDP. |
| `receipts_gdp` | Federal receipts as a percent of GDP. |
| `outlays_gdp` | Federal outlays as a percent of GDP. |
| `deficit_gdp` | Federal surplus or deficit as a percent of GDP. Positive values are surplus, negative values are deficit. |
| `interest_gdp` | Federal interest outlays as a percent of GDP. |
| `*_source` | Source identifier for the fiscal series. |

## `data/models/fiscal_context.csv`

| Column | Meaning |
|---|---|
| `year` | Calendar year in the GDP/fiscal overlapping panel. |
| `gdp_growth` | Annual percentage growth in the Maddison-derived real GDP proxy. |
| `segment_id` | Fitted GDP growth-regime identifier. |
| `segment_regime` | `above_mean` or `below_mean` GDP growth segment. |
| `segment_mean_growth` | Mean GDP growth in the fitted segment. |
| fiscal ratio columns | Same fiscal-ratio columns as `fiscal_ratios.csv`. |

## `data/models/fiscal_growth_correlations.csv`

| Column | Meaning |
|---|---|
| `variable` | Fiscal variable name. |
| `label` | Human-readable fiscal variable label. |
| `n_same_year` | Number of observations used in same-year correlation. |
| `correlation_same_year` | Correlation between annual GDP growth and the fiscal variable in the same year. |
| `n_lag1` | Number of observations used in one-year-lag correlation. |
| `correlation_lag1` | Correlation between annual GDP growth and the fiscal variable lagged one year. |

## `data/models/fiscal_growth_association.csv`

| Column | Meaning |
|---|---|
| `term` | OLS regression term. Fiscal variables enter with one-year lags. |
| `coefficient` | Estimated descriptive association with annual GDP growth. |
| `std_error` | Standard error from the OLS regression. |
| `p_value` | P-value from the OLS regression. |
| `n_observations` | Number of observations used in the regression. |
| `r_squared` | Regression R-squared. |
| `model_note` | Reminder that the model is descriptive only. |

## `data/models/tax_regime_events.csv`

| Column | Meaning |
|---|---|
| `year` | Event year. |
| `event` | Broad federal tax-regime event. |
| `category` | Tax-policy area affected. |
| `direction` | Coarse direction: `increase`, `decrease`, `mixed`, or `base_broadening`. |
| `description` | Short event description. |

## `data/models/tax_event_growth_windows.csv`

| Column | Meaning |
|---|---|
| `year` | Event year. |
| event columns | Event metadata from `tax_regime_events.csv`. |
| `window_years` | Number of years before and after the event used in the window. |
| `n_pre` | Number of pre-event GDP-growth observations. |
| `n_event_window` | Number of observations from the event year through the post-event window. |
| `pre_mean_growth` | Average GDP growth before the event. |
| `event_window_mean_growth` | Average GDP growth during the event/post-event window. |
| `event_window_minus_pre` | Difference between event-window and pre-event average growth. |
