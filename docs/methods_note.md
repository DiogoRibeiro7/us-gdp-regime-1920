# Methods note

## Research design

The project separates two empirical questions.

First, it estimates the long-run trend of United States real GDP using a linear regression on log real GDP:

```text
log(GDP_t) = alpha + beta * year_t + error_t
```

This is a compact way to estimate an average exponential growth path.

Second, it estimates growth regimes using annual real GDP growth. This is more meaningful than applying above/below-mean labels to GDP levels, because the level is non-stationary and mechanically higher in later decades.

## Piecewise regression

The piecewise model assumes that growth is locally stable around a segment mean:

```text
growth_t = mu_j + error_t, for t in segment j
```

The algorithm searches over possible breakpoints using dynamic programming. For each candidate segmentation it computes the within-segment sum of squared errors. The selected model minimises an information criterion, BIC by default.

## Why BIC?

BIC penalises extra segments more strongly than AIC. That is appropriate here because the article should not overfit every recession or temporary rebound. The goal is to identify broad growth regimes, not every business-cycle fluctuation.

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

This is useful when effects appear gradually, reverse, or fade over time.

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
