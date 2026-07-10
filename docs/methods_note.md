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
