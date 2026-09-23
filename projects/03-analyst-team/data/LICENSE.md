# Data licence

This project **adds no source data**. It reads Project 02's filings and labelled
questions by path, and never copies them:

| Field | Value |
|---|---|
| File | `../../02-sec-filings/data/raw/*.html`, `../../02-sec-filings/data/sources.json`, `../../02-sec-filings/data/questions.json` |
| Publisher | The U.S. Securities and Exchange Commission, on EDGAR (<https://www.sec.gov/edgar>) |
| Source URL | One per filing, in `../../02-sec-filings/data/sources.json` |
| Fetched on | See `filed` and the fetch record in Project 02's `sources.json` |
| Size | 1.2 MB of HTML over eight files, 92 KB to 243 KB each |
| Changes | None here. This project reads those files; it does not write them. |

**Licence:** the filings are public filings published by the SEC. The companies
wrote them, so they are not U.S. government works. See
`../../02-sec-filings/data/LICENSE.md` for the full statement, which governs
them wherever they are read from.

**Credit:** every filing's company, CIK, accession number and URL are recorded in
Project 02's `sources.json`, and the notebook prints them on request.

Nothing here identifies a private person, and nothing here is investment advice.

`recorded/` is ours: the model replies of one real run of this notebook, kept so
that every step works with no model installed. It holds replies and provenance,
never a key, never anything a learner typed.
