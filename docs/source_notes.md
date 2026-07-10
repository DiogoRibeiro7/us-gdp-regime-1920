# Source notes

## Maddison Project Database 2023

The Maddison Project Database is used as the default source because this project begins in 1920. The 2023 release covers 169 countries and extends up to 2022. It includes long-run GDP per capita and population data. For this project, total real GDP is constructed as real GDP per capita multiplied by population.

Recommended citation from the source:

Bolt, Jutta and Jan Luiten van Zanden. Maddison style estimates of the evolution of the world economy: A new 2023 update. Journal of Economic Surveys.

## FRED / BEA GDPCA

FRED series `GDPCA` is used as a validation source from 1929 onward. It reports annual United States real GDP in billions of chained 2017 dollars, sourced from the U.S. Bureau of Economic Analysis.

## FRED / OMB fiscal ratios

The fiscal context layer uses FRED-hosted annual federal budget and debt ratios
derived from OMB historical tables and GDP. The current implementation loads
gross federal debt, debt held by the public, federal receipts, federal outlays,
federal surplus or deficit, and federal interest outlays as percent of GDP.

These are used as contextual macro-fiscal variables. They are not instruments
or exogenous policy shocks.

## IRS tax-rate history

The tax-regime event catalog is intentionally broad. IRS SOI Historical Table 23
is the preferred reference for extending the project into statutory individual
income-tax bracket rates and tax bases. That extension should be kept separate
from the current event-window catalog because statutory rates and effective
fiscal receipts answer different empirical questions.

## Narrative tax-shock catalog

The dynamic tax-effects notebook uses a curated tax-shock catalog with signed
ordinal treatment values and narrative classifications. The classification is
not a substitute for a full archival narrative dataset. It is a transparent
starting point for separating plausibly exogenous long-run reforms from
deficit-reduction packages, wartime finance, countercyclical stimulus, and
mixed-motivation reforms.

Future versions should replace ordinal shock values with estimated revenue
effects as a percent of GDP and should document announcement, phase-in, and
sunset timing for each major provision.

## Distributional wage and tax-burden sources

The wage/GDP comparison uses BEA real GDP per capita and BLS real earnings
series from FRED. Real median weekly earnings are narrower than national income:
they refer to full-time wage and salary workers and therefore do not capture
capital income, business income, transfers, or all household members.

The tax-burden shift analysis uses federal receipt composition from BEA/FRED,
IRS/FRED top and bottom statutory individual income-tax rates, and BLS Consumer
Expenditure Survey income and federal income-tax amounts by before-tax income
quintile. The quintile data begin in the 1980s and measure average federal
income-tax amounts in consumer units, not full federal tax incidence.

## Practical implication

Use Maddison for the full 1920-onward history. Use FRED/BEA for the modern
national-account overlap. Use FRED/OMB fiscal ratios and tax-regime events as
descriptive context, not causal proof. The article should report any relevant
difference between the growth-rate series before drawing regime conclusions.
