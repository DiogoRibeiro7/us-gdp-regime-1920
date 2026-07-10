# Publishing to Zenodo (GitHub release → DOI)

This repository is prepared for archival on Zenodo. A `LICENSE` (CC-BY-4.0),
`CITATION.cff`, and `.zenodo.json` are already in place, so Zenodo will pick up
the correct title, authors, description, license, and keywords automatically.

The recommended path mints a **versioned DOI** from a GitHub release. The Zenodo
deposit itself needs your browser login, so the web steps below are for you to
run; everything on the repository side is done.

## One-time setup

1. Sign in at <https://zenodo.org> (use "Log in with GitHub").
2. Go to <https://zenodo.org/account/settings/github/> and click **Sync** if
   needed.
3. Find `DiogoRibeiro7/us-gdp-regime-1920` in the repository list and flip the
   toggle **ON**. This tells Zenodo to archive future releases of this repo.

## Publish a release

1. Make sure `main` is pushed and green (CI passing):
   ```bash
   git push origin main
   ```
2. Create an annotated tag and a GitHub release. A first public release is
   conventionally `v1.0.0` (matches the version in `CITATION.cff` and
   `pyproject.toml`):
   ```bash
   git tag -a v1.0.0 -m "First public release"
   git push origin v1.0.0
   ```
   Then on GitHub: **Releases → Draft a new release → choose tag v1.0.0 →
   Publish release**. (Or `gh release create v1.0.0 --title "v1.0.0" --notes "First public release"`.)
3. Zenodo detects the release within a minute or two and creates the deposit
   automatically, reading metadata from `.zenodo.json`.

## After the deposit

1. Open the new record on Zenodo and review the metadata. If you have an
   **ORCID**, add it to your Zenodo profile and to the author on the record (and
   uncomment the `orcid:` line in `CITATION.cff` for next time).
2. Zenodo issues two DOIs:
   - a **concept DOI** that always resolves to the latest version — use this in
     the README badge and the LinkedIn post;
   - a **version DOI** specific to `v1.0.0`.
3. Copy the DOI and finish the loop in the repo:
   - Replace `RECORD_ID` in the `README.md` badge and citation.
   - Commit and push.

## Notes

- Zenodo archives a **snapshot of the tagged release** (source + committed
  files). Raw downloaded data and generated model CSVs/figures are intentionally
  gitignored, so they are not in the archive; the pipeline regenerates them and
  the compiled report PDF (`reports/us_gdp_regime_report.pdf`) is committed.
- To frame the deposit as a paper rather than software, you can change
  **Upload type** to *Publication → Report* in the Zenodo web form; the DOI is
  citable either way. The default here is `software`, which matches a
  GitHub-archived repository.
- Every subsequent release you publish gets a new version DOI under the same
  concept DOI, so the citation stays stable as the work evolves.

## Manual alternative (no GitHub integration)

If you prefer not to link accounts: on Zenodo click **New upload**, drag in a zip
of the repository (or just `reports/us_gdp_regime_report.pdf`), and fill the
metadata by hand using `.zenodo.json` as the reference. This still mints a DOI
but does not auto-update on future releases.
