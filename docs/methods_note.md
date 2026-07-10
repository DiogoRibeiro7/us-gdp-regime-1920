# Methods note

## Research design

The project separates two empirical questions.

First, it estimates the long-run trend of United States real GDP using a linear regression on log real GDP:

```text
log(GDP_t) = alpha + beta * year_t + error_t
```

This is a compact way to estimate an average exponential growth path. The slope
is reported with Newey-West heteroskedasticity- and autocorrelation-consistent
(HAC) standard errors, because annual macroeconomic residuals are serially
correlated and ordinary OLS standard errors would overstate precision.

Second, it estimates growth regimes using annual real GDP growth. This is more meaningful than applying above/below-mean labels to GDP levels, because the level is non-stationary and mechanically higher in later decades.

## Unit-root diagnostics

The high R-squared of the log-trend regression must not be read as evidence for a
deterministic trend. Log real GDP is close to a unit-root process, and a straight
line mechanically fits a near-integrated series well. The pipeline therefore runs
two complementary tests on both the log level and the growth series:

1. the augmented Dickey-Fuller (ADF) test, whose null is a unit root, and
2. the KPSS test, whose null is stationarity.

In the current data the log level is consistent with a unit root while growth is
stationary. This is the formal justification for segmenting growth rather than
the level. Results are written to `data/models/unit_root_tests.csv`.

## Piecewise regression

The piecewise model assumes that growth is locally stable around a segment mean:

```text
growth_t = mu_j + error_t, for t in segment j
```

The algorithm searches over possible breakpoints using dynamic programming. For each candidate segmentation it computes the within-segment sum of squared errors. The selected model minimises an information criterion, BIC by default.

The information criterion counts each segment mean, each break location, and the
common residual variance as free parameters, so a model with `k` segments carries
`2k` parameters. This keeps the Gaussian BIC and AIC complete rather than off by
one.

## Why BIC?

BIC penalises extra segments more strongly than AIC. That is appropriate here because the article should not overfit every recession or temporary rebound. The goal is to identify broad growth regimes, not every business-cycle fluctuation.

## Recursive refinement

A single global segmentation assumes one residual variance for the whole sample.
That assumption fails for United States growth: the 1929-1945 swings inflate the
pooled variance so much that calmer postwar mean shifts are never selected, and
the global fit leaves 1950 onward as one long block. The pipeline therefore
applies a recursive refinement (`fit_recursive_growth_regimes`, enabled by
`model.recursive_refinement`): after the global fit, each segment is re-segmented
on its own observations and its own residual variance, and split when the
criterion supports it. Recursion is bounded by `model.max_recursion_depth`.

On the current data this splits the postwar era at 2000 into a high-growth
1950-2000 regime and a slower 2001-2022 regime (the post-2000 slowdown). The
split is corroborated three ways --- postwar subsample under BIC, postwar
subsample under AIC, and the full sample under AIC all agree --- and the single
postwar break is significant on the postwar subsample's own scale
(`postwar_break_tests.csv`), while no further postwar break is. The plain global
segmentation is retained as `regime_segments_global.csv` for reference, and the
decomposition is written to `postwar_decomposition.csv`.

## Are the breaks statistically supported?

The number of regimes is not taken on faith from the information criterion. Two
inference layers accompany it:

1. A sequential `supF(l+1 | l)` test compares the optimal `l`-segment and
   `(l+1)`-segment models. Because the break date is estimated, the statistic
   does not follow a standard F distribution, so its p-value is obtained by a
   parametric bootstrap that simulates from the fitted smaller model. Results are
   written to `data/models/break_significance_tests.csv`, and the full
   selection curve (SSE, BIC, AIC by segment count) to
   `data/models/segmentation_selection.csv`.
2. A residual bootstrap re-segments resampled series to produce percentile
   confidence intervals for each break year, written to
   `data/models/break_date_confidence_intervals.csv`. This distinguishes breaks
   whose dates are sharp from breaks whose timing is poorly identified.

## Above/below mean labels

A segment is labelled `above_mean` if its segment mean growth is greater than or equal to the full-sample mean growth. It is labelled `below_mean` otherwise.

This is descriptive. It does not prove causality.

## Robustness checks

The article should include at least four checks:

1. Run the piecewise model with several minimum segment sizes: 4, 5, 7, and 10 years.
2. Run the model with BIC and AIC.
3. Compare Maddison-derived growth rates with FRED/BEA growth rates from 1929 onward.
4. Refit after excluding World War II years to test whether mobilisation dominates breakpoint selection.

## Fiscal and tax-regime context

The optional fiscal layer adds federal debt, receipts, outlays, deficit/surplus,
and interest outlays as percent of GDP. These series are merged onto annual GDP
growth by calendar year and summarized with:

1. same-year fiscal/GDP-growth correlations,
2. one-year-lag fiscal/GDP-growth correlations,
3. a compact OLS association model using one-year-lag fiscal ratios,
4. event windows around broad federal tax-regime changes.

This layer is descriptive. Public debt, deficits, receipts, outlays, and tax law
are endogenous to recessions, wars, inflation, monetary policy, and GDP itself.
The fiscal tables can structure historical interpretation, but they do not
identify causal tax or debt effects on GDP.

## Dynamic tax-regime effects

The tax-effects layer asks whether GDP growth changes with a delay after
federal tax-regime changes. It uses three complementary designs.

First, local projections estimate a separate regression for each horizon:

```text
growth_(t+h) = alpha_h + beta_h * tax_shock_t + controls_t + error_(t+h)
```

This is useful when effects appear gradually, reverse, or fade over time. Each
horizon is estimated with HAC standard errors whose Newey-West lag length grows
with the horizon, because the horizon-`h` local-projection residual is serially
correlated up to order `h` by construction (Jordà, 2005).

Second, distributed-lag regressions include current and lagged tax shocks in one
model:

```text
growth_t = alpha + beta_0 * shock_t + beta_1 * shock_(t-1) + ... + controls_t + error_t
```

This compresses delayed responses into a current-year model and reports
cumulative coefficients through each lag.

Third, dynamic event studies compare each event-relative year with the event's
own pre-event growth average. This is a transparent visual check for delayed
patterns around tax-law dates.

The tax-shock catalog separates all events from a smaller set classified as
plausibly exogenous long-run reforms. Causal language should be limited to that
subset and still treated as model-dependent. Deficit-reduction packages,
wartime finance, recession responses, and mixed reforms should not be pooled
with long-run reforms without showing the classification.

## Distributional tax burden and real wages

The distributional layer separates aggregate output from worker buying power.
Real GDP per capita is indexed against real median weekly earnings and real
hourly compensation. A widening index gap means aggregate real output per person
is rising faster than the real earnings measure.

Tax-burden shifts are measured with three proxies:

1. receipt composition: social-insurance contributions versus personal and
   corporate income-tax receipts,
2. statutory progressivity: top minus bottom regular individual income-tax
   bracket rates,
3. income-quintile federal income-tax rates from BLS Consumer Expenditure data.

These proxies are useful but incomplete. They do not fully estimate tax
incidence across income classes. Payroll tax incidence, refundable credits,
employer-side contributions, corporate tax incidence, capital income, state and
local taxes, and transfers all matter for a full burden analysis.

The association screen regresses GDP growth, median earnings growth, and the
GDP/wage gap on one-year-lagged tax-burden proxies. It is designed to flag
patterns for interpretation, not to establish causality.

## Historical interpretation

The regimes should be interpreted with historical care. Likely contextual periods include:

- post-World War I and 1920s expansion,
- the Great Depression,
- World War II mobilisation,
- postwar adjustment,
- the postwar growth era,
- the productivity slowdown after the early 1970s,
- Volcker disinflation and early 1980s recession,
- the 1990s expansion,
- the Global Financial Crisis,
- COVID-19 and recovery.

The statistical model can find regimes, but historical evidence is required to explain them.
