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
| `slope` | Annual slope in log real GDP (`beta`). |
| `r_squared` | R-squared of the log trend regression. High values reflect persistence, not evidence of a deterministic trend. |
| `annualised_growth_rate` | Approximate annual trend growth rate, computed as `exp(slope) - 1`. |
| `slope_std_error` | Newey-West (HAC) standard error of the slope. |
| `slope_t_statistic` | HAC t-statistic of the slope. |
| `slope_p_value` | HAC p-value of the slope. |
| `n_observations` | Number of annual observations used. |
| `hac_lags` | Newey-West truncation lag. |

## `data/models/regime_segments.csv`

Headline regimes from the recursive-refinement model (see `regime_segments_global.csv`
for the plain global fit).

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

## `data/models/regime_segments_global.csv`

Plain global segmentation (one pooled residual variance), retained as a
reference for the recursive headline model. Same columns as
`regime_segments.csv`.

## `data/models/unit_root_tests.csv`

| Column | Meaning |
|---|---|
| `series` | Tested series (`log_real_gdp` or `gdp_growth`). |
| `description` | Human-readable series description. |
| `adf_regression` | ADF deterministic terms (`ct` = constant and trend, `c` = constant). |
| `adf_stat`, `adf_pvalue` | Augmented Dickey-Fuller statistic and p-value (null: unit root). |
| `adf_used_lag`, `adf_nobs` | Lag order selected by AIC and effective observations. |
| `adf_rejects_unit_root_5pct` | Whether ADF rejects the unit root at 5%. |
| `kpss_stat`, `kpss_pvalue` | KPSS statistic and p-value (null: stationarity). |
| `kpss_used_lag` | KPSS bandwidth. |
| `kpss_rejects_stationarity_5pct` | Whether KPSS rejects stationarity at 5%. |

## `data/models/segmentation_selection.csv`

Model-selection curve behind the regime count.

| Column | Meaning |
|---|---|
| `n_segments`, `n_breaks` | Number of segments and breaks. |
| `sse` | Optimal within-segment SSE for that segment count. |
| `n_parameters` | Free-parameter count (`2 * n_segments`). |
| `bic`, `aic` | Information-criterion values; the minimum selects the regime count. |

## `data/models/break_significance_tests.csv`

Sequential `supF(l+1 | l)` tests for the global model. (`postwar_break_tests.csv`
has the same schema for the postwar subsample.)

| Column | Meaning |
|---|---|
| `segments_null`, `segments_alt` | Segment counts of the nested models being compared. |
| `f_statistic` | F-style statistic for the additional break. |
| `bootstrap_p_value` | Parametric-bootstrap p-value (break date is estimated, so distribution is non-standard). |
| `n_bootstrap` | Bootstrap replications. |
| `ssr_null`, `ssr_alt` | Optimal SSE of the smaller and larger models. |

## `data/models/break_date_confidence_intervals.csv`

Residual-bootstrap confidence intervals for the global model's break years.

| Column | Meaning |
|---|---|
| `break_index` | Ordinal break number. |
| `point_break_year` | Point-estimate break year. |
| `bootstrap_median_year` | Median bootstrap break year. |
| `ci_low_year`, `ci_high_year` | 90% percentile interval. |
| `bootstrap_std_years` | Bootstrap standard deviation of the break year (dating precision). |
| `n_bootstrap` | Bootstrap replications. |

## `data/models/postwar_decomposition.csv`

Re-segmentation of the postwar era three ways (postwar subsample under BIC and
AIC, and the full sample under AIC).

| Column | Meaning |
|---|---|
| `sample` | `postwar` or `full`. |
| `criterion` | `bic` or `aic`. |
| `start_year`, `end_year`, `n_observations` | Segment span and length. |
| `mean_growth` | Segment mean annual growth. |
| `regime` | `above_mean` or `below_mean`. |

## `data/models/regime_robustness.csv`

Regime segmentation re-estimated across robustness scenarios.

| Column | Meaning |
|---|---|
| `scenario_id` | Scenario label (e.g. `min_segment_size_7`, `criterion_aic`, `exclude_...`). |
| `criterion`, `min_segment_size` | Settings used in the scenario. |
| `excluded_years` | Years dropped before refitting (empty if none). |
| `segment_id`, `start_year`, `end_year`, `mean_growth`, `regime` | Fitted segment summary. |

## `data/models/recurring_break_years.csv`

Break years clustered across robustness scenarios within a two-year tolerance.

| Column | Meaning |
|---|---|
| `cluster_id` | Cluster identifier. |
| `representative_break_year` | Modal break year in the cluster. |
| `min_break_year`, `max_break_year` | Range of years in the cluster. |
| `n_breaks` | Number of contributing breaks. |
| `n_scenarios` | Number of scenarios in which the break appears. |
| `scenarios` | Comma-separated contributing scenario ids. |

## `data/models/report_numbers.json`

A flat mapping of every statistic quoted in the written report/article to its
formatted value, generated by `us-gdp-regimes export-report-numbers`. The report
inputs the corresponding LaTeX macros so prose cannot drift from the outputs.

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

## `data/models/tax_shock_catalog.csv`

| Column | Meaning |
|---|---|
| `year` | Tax-regime event year. |
| `event` | Federal tax-regime event name. |
| `tax_type` | Main tax area affected. |
| `direction` | Coarse direction: `increase`, `decrease`, `mixed`, or `base_broadening`. |
| `shock_value` | Ordinal signed treatment proxy. Positive values denote tax increases; negative values denote tax cuts. This is not a revenue estimate. |
| `permanence` | `temporary`, `permanent`, or `mixed`. |
| `anticipation_years` | Years between expected/announced policy and implementation, when coded. |
| `implementation_lag_years` | Approximate implementation delay retained for timing analysis. |
| `narrative_classification` | Historical motivation class used to separate reform, deficit, wartime, stimulus, and mixed events. |
| `plausibly_exogenous` | Boolean flag for the subset most relevant to causal interpretation. |
| `description` | Short event description. |

## `data/models/tax_effect_panel.csv`

| Column | Meaning |
|---|---|
| `year` | Calendar year. |
| GDP columns | GDP growth and fitted regime labels from the prepared GDP series. |
| fiscal columns | Optional fiscal context ratios when available. |
| `tax_shock_all` | Sum of signed tax-shock values in the year. |
| `tax_shock_exogenous` | Sum of signed shocks classified as plausibly exogenous. |
| `tax_increase_all` | Positive tax-shock component in the year. |
| `tax_cut_all` | Absolute value of negative tax-shock component in the year. |
| `tax_event_count` | Number of catalogued tax events in the year. |
| `tax_exogenous_event_count` | Number of plausibly exogenous tax events in the year. |

## `data/models/tax_local_projections.csv`

| Column | Meaning |
|---|---|
| `model` | `local_projection`. |
| `shock_column` | Tax-shock treatment series used in the regression. |
| `horizon` | Years after the tax-regime shock. |
| `term` | Estimated treatment term. |
| `coefficient` | Estimated association between the tax shock and future annual GDP growth at the horizon. |
| `std_error` | HAC standard error. |
| `p_value` | P-value for the coefficient. |
| `conf_low` | Lower bound of approximate 95 percent confidence interval. |
| `conf_high` | Upper bound of approximate 95 percent confidence interval. |
| `n_observations` | Observations used at the horizon. |
| `r_squared` | Regression R-squared. |
| `controls` | Included control columns. |
| `model_note` | Causal caveat. |

## `data/models/tax_distributed_lags.csv`

| Column | Meaning |
|---|---|
| local-projection columns | Same coefficient metadata as `tax_local_projections.csv`. |
| `term` | Current or lagged tax-shock term. |
| `cumulative_coefficient_through_lag` | Sum of tax-shock coefficients from lag 0 through the current lag. |

## `data/models/tax_dynamic_event_study.csv`

| Column | Meaning |
|---|---|
| `relative_year` | Year relative to the tax-regime event. |
| `n_events` | Number of events contributing to the relative-year estimate. |
| `mean_growth` | Mean GDP growth in that event-relative year. |
| `mean_growth_minus_pre` | Mean GDP growth minus each event's own pre-event average. |
| `std_growth_minus_pre` | Standard deviation of event-level differences. |
| `std_error` | Standard error of event-level differences. |
| `conf_low` | Lower approximate 95 percent confidence bound. |
| `conf_high` | Upper approximate 95 percent confidence bound. |
| `sample` | `all_events` or `plausibly_exogenous`. |

## `data/models/distributional_raw_series.csv`

| Column | Meaning |
|---|---|
| `year` | Calendar year. |
| `real_gdp_per_capita` | BEA real GDP per capita, annualized from FRED quarterly observations. |
| `real_median_weekly_earnings` | BLS real median usual weekly earnings for full-time wage and salary workers, annualized from FRED quarterly observations. |
| `real_hourly_compensation` | BLS nonfarm business real hourly compensation index, annualized from FRED quarterly observations. |
| receipt columns | Federal current tax receipts, personal current taxes, social-insurance contributions, and corporate income taxes. |
| statutory rate columns | IRS/FRED top and bottom regular individual income-tax bracket rates. |
| quintile columns | BLS Consumer Expenditure income and federal income-tax amounts by before-tax income quintile. |

## `data/models/wage_gdp_gap.csv`

| Column | Meaning |
|---|---|
| GDP/wage level columns | Annual real GDP per capita, real median weekly earnings, and real hourly compensation. |
| `*_index` | Series indexed to a common base year, usually 1979 when available. |
| `*_growth` | Annual percent change. |
| `gdp_per_capita_minus_median_earnings_index` | Real GDP per capita index minus real median weekly earnings index. |
| `gdp_per_capita_minus_hourly_compensation_index` | Real GDP per capita index minus real hourly compensation index. |
| `index_base_year` | Base year used for the indexes. |

## `data/models/tax_burden_shift.csv`

| Column | Meaning |
|---|---|
| receipt columns | Federal personal, corporate, and social-insurance receipt series. |
| `social_insurance_share` | Social-insurance contributions as a share of selected federal receipt categories. |
| `personal_tax_share` | Personal current taxes as a share of selected federal receipt categories. |
| `corporate_tax_share` | Corporate income taxes as a share of selected federal receipt categories. |
| `income_corporate_tax_share` | Personal plus corporate taxes as a share of selected federal receipt categories. |
| `statutory_rate_spread` | Top individual income-tax bracket rate minus bottom bracket rate. |
| `top_bottom_rate_ratio` | Top individual income-tax bracket rate divided by bottom bracket rate. |

## `data/models/quintile_tax_rates.csv`

| Column | Meaning |
|---|---|
| `federal_income_tax_rate_q1` through `q5` | Federal income taxes divided by before-tax income for each income quintile. Negative values can occur when refundable credits exceed tax liability. |
| `q5_minus_q1_federal_income_tax_rate` | Highest quintile rate minus lowest quintile rate. |
| `q5_minus_middle_federal_income_tax_rate` | Highest quintile rate minus middle quintile rate. |
| `q5_minus_bottom80_federal_income_tax_rate` | Highest quintile rate minus the average rate across the bottom four quintiles. |

## `data/models/distributional_context.csv`

| Column | Meaning |
|---|---|
| GDP growth columns | Maddison-derived annual GDP growth. |
| wage/GDP columns | Indexed wage/GDP gap measures from `wage_gdp_gap.csv`. |
| tax-shift columns | Receipt-composition and statutory progressivity proxies from `tax_burden_shift.csv`. |
| quintile tax-rate columns | Federal income-tax rates and spreads from `quintile_tax_rates.csv`. |

## `data/models/distributional_growth_associations.csv`

| Column | Meaning |
|---|---|
| `outcome` | GDP growth, real median earnings growth, or GDP/wage gap outcome. |
| `predictor` | Lagged tax-burden shift proxy. |
| `lag` | Predictor lag, currently one year. |
| `coefficient` | Single-predictor lagged association coefficient. |
| `std_error` | HAC standard error. |
| `p_value` | P-value for the coefficient. |
| `conf_low` | Lower approximate 95 percent confidence bound. |
| `conf_high` | Upper approximate 95 percent confidence bound. |
| `n_observations` | Observations used. |
| `r_squared` | Regression R-squared. |
| `model_note` | Causal caveat. |
