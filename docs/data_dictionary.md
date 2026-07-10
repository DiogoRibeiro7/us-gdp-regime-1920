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
