# LinkedIn post — technical / methods-forward

> Draft. Replace `https://doi.org/10.5281/zenodo.21302054` and the release URL after the Zenodo deposit, then
> paste the body below into LinkedIn. Suggested first comment holds the links so
> the main post stays clean.

---

**The neat trend line through 100 years of U.S. log GDP is a statistical trap — and fixing it changes the story.**

I just released a fully reproducible study of U.S. real GDP growth since 1920. A few methods notes for the econometrics-minded:

𝟭. 𝗧𝗵𝗲 𝗹𝗲𝘃𝗲𝗹 𝗶𝘀 𝗻𝗲𝗮𝗿𝗹𝘆 𝗮 𝘂𝗻𝗶𝘁 𝗿𝗼𝗼𝘁. A linear trend fits log GDP with R² ≈ 0.99, but that "fit" is mechanical: ADF cannot reject a unit root (p ≈ 0.99) while KPSS rejects trend-stationarity. Growth, not the level, is the stationary object — so that's what I model. (Perron's 1989 warning that unmodelled breaks bias unit-root tests is taken seriously throughout.)

𝟮. 𝗥𝗲𝗴𝗶𝗺𝗲𝘀, 𝗻𝗼𝘁 𝗮 𝘁𝗿𝗲𝗻𝗱. An exact dynamic-programming segmentation with a BIC penalty finds the Depression, wartime mobilisation, and postwar eras. But a single pooled variance lets the violent 1929–45 swings dominate and hides everything after — it collapses 1950–2022 into one 73-year block.

𝟯. 𝗩𝗮𝗿𝗶𝗮𝗻𝗰𝗲 𝗽𝗼𝗼𝗹𝗶𝗻𝗴 𝗶𝘀 𝘁𝗵𝗲 𝗯𝘂𝗴. A recursive refinement re-segments each regime on *its own* variance scale. The postwar era then splits cleanly at ~2000 into a high-growth 1950–2000 phase (~3.6%/yr) and the post-2000 slowdown (~1.9%/yr). The split is corroborated three ways (postwar-BIC, postwar-AIC, full-sample AIC) and is significant on the postwar subsample (bootstrap p ≈ 0.045). The global model's tell was already there: its 1950 break had a bootstrap CI running to the late 1980s.

𝟰. 𝗨𝗻𝗰𝗲𝗿𝘁𝗮𝗶𝗻𝘁𝘆, 𝗻𝗼𝘁 𝗷𝘂𝘀𝘁 𝗽𝗼𝗶𝗻𝘁 𝗲𝘀𝘁𝗶𝗺𝗮𝘁𝗲𝘀. Sequential supF break tests (parametric bootstrap), break-date confidence intervals, and a robustness grid over segment sizes / BIC-AIC / WWII-exclusion separate the firm breaks (1933 recurs in every scenario) from the fragile ones.

𝟱. 𝗕𝗲𝘆𝗼𝗻𝗱 𝗮𝗴𝗴𝗿𝗲𝗴𝗮𝘁𝗲𝘀. Local projections (Jordà) screen the dynamic response of growth to narrative tax-regime shocks (Romer–Romer style), and I set aggregate GDP per capita against real median earnings — the productivity–pay gap that aggregate growth hides.

𝗧𝗵𝗲 𝗿𝗲𝗽𝗿𝗼𝗱𝘂𝗰𝗶𝗯𝗶𝗹𝗶𝘁𝘆 𝗮𝗻𝗴𝗹𝗲: every number in the paper is machine-generated from the model outputs and injected into the LaTeX as macros — the prose literally cannot drift from the estimates. Typed Python, tests, CI.

Feedback from anyone working on structural breaks, unit-root testing, or long-run growth is very welcome.

📄 Paper + code (DOI): https://doi.org/10.5281/zenodo.21302054
💻 GitHub: https://github.com/DiogoRibeiro7/us-gdp-regime-1920

#Econometrics #Economics #TimeSeries #DataScience #ReproducibleResearch #Macroeconomics #StructuralBreaks #OpenScience

---

## Suggested first comment (put the links here to keep the post clean)

Full write-up (paper + reproducible pipeline) archived on Zenodo: https://doi.org/10.5281/zenodo.21302054
Code: https://github.com/DiogoRibeiro7/us-gdp-regime-1920
Methods: unit-root diagnostics (ADF/KPSS), DP segmentation with recursive refinement, bootstrap supF break tests, Jordà local projections, all with HAC inference.

## Shorter variant (if you want a tighter post)

The tidy trend line through a century of U.S. log GDP is a statistical trap: the level is indistinguishable from a unit root, so growth is the right object. Modelling growth as regimes — and fixing a variance-pooling flaw that hides the post-2000 slowdown behind the 1929–45 chaos — resolves U.S. history into 6 statistically supported eras, ending in a distinct post-2000 slowdown. Fully reproducible; every number is generated from the outputs.

📄 https://doi.org/10.5281/zenodo.21302054 · 💻 https://github.com/DiogoRibeiro7/us-gdp-regime-1920
