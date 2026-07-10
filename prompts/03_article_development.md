# Prompts for article development

Use these prompts with a writing or research agent after the code and notebooks have produced final tables and figures.

---

## Prompt 1 — Research-grounded article plan

You are writing a data-driven article about United States GDP growth regimes from 1920 onward.

The repository has produced:

- a log real GDP trend regression,
- annual real GDP growth rates,
- piecewise growth regimes,
- above-mean and below-mean segment labels,
- Maddison historical data from 1920 onward,
- FRED/BEA validation from 1929 onward.

Create a detailed article plan.

Requirements:

1. The argument must be empirical and sober.
2. Do not claim that GDP growth is explained by one single political ideology.
3. Do not claim causality from the piecewise regression alone.
4. Explain why GDP levels are not used for above/below-mean classification.
5. Explain why Maddison is used for the 1920 start date.
6. Explain why FRED/BEA is used as validation from 1929 onward.
7. Include a section on limitations.

Deliverable:

- detailed outline with section titles,
- paragraph-level summary for each section,
- list of figures and tables,
- list of claims that require historical sources.

---

## Prompt 2 — Write the full article draft

Write a full article in English using the final outputs from this repository.

Working title:

**The United States did not grow at one speed: GDP regimes from 1920 onward**

Required style:

- journalistic but data-driven,
- clear and sober,
- technical enough for a data science audience,
- readable for non-specialists,
- no inflated claims,
- no ideological shortcuts.

Required structure:

1. Opening thesis.
2. Data and source choices.
3. Why growth regimes matter.
4. Long-run GDP trend regression.
5. Piecewise growth regimes.
6. Above-mean and below-mean periods.
7. Historical interpretation.
8. Robustness and limitations.
9. Conclusion.

Required insertions:

- include placeholders for figures:
  - `[Figure 1: Log real GDP trend]`
  - `[Figure 2: GDP growth regimes]`
  - `[Table 1: Regime summary]`
- include a short methods box,
- include a clear caveat that statistical breaks are not causal proof.

---

## Prompt 3 — Strengthen the historical interpretation

Review the article draft and improve the historical interpretation.

Use the statistical regimes as the structure, but connect them carefully to known economic periods.

Potential periods:

- the 1920s and the lead-up to the Great Depression,
- the Great Depression and New Deal years,
- World War II mobilisation,
- postwar adjustment,
- postwar expansion,
- productivity slowdown after the early 1970s,
- inflation and disinflation period,
- late 20th-century expansion,
- Global Financial Crisis,
- COVID-19 shock and recovery.

Rules:

1. Every historical claim must be sourceable.
2. Avoid deterministic language.
3. Use phrases such as `consistent with`, `coincides with`, and `suggests`, where appropriate.
4. Do not imply the model identifies policy causality.

Deliverable:

- revised interpretation section,
- list of claims requiring citations,
- list of possible sources to consult.

---

## Prompt 4 — Peer review the article

Act as a critical peer reviewer.

Review the article for:

1. statistical overclaiming,
2. unclear data definitions,
3. weak explanation of piecewise regression,
4. missing robustness checks,
5. unsupported historical claims,
6. confusing figures or tables,
7. excessive political framing,
8. weak conclusion.

Deliverable:

- major issues,
- minor issues,
- required revisions,
- optional improvements,
- final recommendation: accept, revise, or reject.

---

## Prompt 5 — Produce final Medium-ready article

Prepare the final article for Medium.

Requirements:

1. Use an engaging but sober title.
2. Add a subtitle.
3. Add figure placeholders.
4. Include concise captions.
5. Include a short methods section.
6. Include a data and code availability note.
7. Include tags.
8. Keep equations minimal.
9. Avoid academic stiffness.
10. Keep claims tied to the evidence.

Deliverable:

- final article in Markdown,
- title,
- subtitle,
- tags,
- suggested social media teaser.
