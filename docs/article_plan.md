# Article plan

## Working title

**The United States did not grow at one speed: GDP regimes from 1920 onward**

## Core argument

The article argues that a single average growth rate is an incomplete description
of United States real GDP after 1920. The empirical workflow uses Maddison
historical estimates for the long-run series, validates overlapping growth rates
against FRED/BEA GDPCA from 1929 onward, estimates a log real GDP trend, and then
identifies piecewise growth regimes. The regimes provide structure for historical
interpretation, but the statistical breakpoints are not treated as causal proof.

## Section plan

### 1. Opening thesis

Introduce the problem with treating long-run GDP growth as one stable speed.
Explain that the article separates trend growth from regime shifts in annual
growth rates.

### 2. Data and source choices

Explain why Maddison is used for the 1920 start date: it provides long-run GDP
per capita and population estimates. Explain why FRED/BEA GDPCA is used as a
validation source: it is the modern national accounts benchmark but begins in
1929 for annual real GDP.

### 3. Why growth regimes matter

Explain why the classification uses annual growth rates rather than GDP levels.
GDP levels trend upward over time, so level-based above/below-average labels
would mostly distinguish early years from late years.

### 4. Long-run trend regression

Present the log real GDP trend model and the annualised trend-growth estimate
from `article_assets/trend_summary.md`. Emphasize that the trend is a compact
summary, not a claim that every period grew at the same speed.

### 5. Piecewise growth regimes

Present `article_assets/regime_table.md` and `[Figure 2: GDP growth regimes]`.
Explain that each segment has one mean growth rate and is labelled above or
below the full-sample mean.

### 6. Historical interpretation

Use the regime sequence as an organizing device. Discuss likely context such as
the Great Depression, World War II mobilisation, postwar adjustment, postwar
expansion, productivity slowdown, disinflation, the Global Financial Crisis, and
COVID-19. Use cautious language: `coincides with`, `is consistent with`, and
`suggests`.

### 7. Robustness and validation

Discuss BIC versus AIC, minimum segment-size sensitivity, exclusion of unusual
historical windows such as 1941-1945, and Maddison/FRED overlap diagnostics.
Stable break years can be described as recurring across modelling choices.

### 8. Limitations

State that Maddison and BEA/FRED are not identical accounting systems, that
piecewise regression is descriptive, that annual data hide within-year dynamics,
and that historical causality requires additional evidence.

### 9. Conclusion

Return to the main claim: long-run GDP growth is better read as a sequence of
regimes than as one constant speed, while recognizing that the model structures
interpretation rather than proving causes.

## Figures and tables

- `[Figure 1: Log real GDP trend]`
- `[Figure 2: GDP growth regimes]`
- `[Figure 3: Maddison versus FRED growth comparison]`
- `[Table 1: Regime summary]`
- `[Table 2: Trend regression summary]`
- Optional robustness table of recurring break years.

## Claims requiring historical sources

- Great Depression chronology and macroeconomic contraction.
- New Deal period policy context.
- World War II mobilisation and demobilisation.
- Postwar expansion and productivity performance.
- 1970s oil shocks and productivity slowdown.
- Volcker disinflation and early 1980s recession.
- Global Financial Crisis chronology.
- COVID-19 shock and recovery.
