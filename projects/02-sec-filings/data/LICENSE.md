# Data licence

`raw/*.html` holds **Item 1A, "Risk Factors"**, cut from the most recent Form
10-K annual report of eight companies: Apple, Microsoft, NVIDIA, Tesla,
Coca-Cola, Nike, MercadoLibre and Airbnb. `sources.json` gives, for every file,
the company, its SEC CIK, the accession number, the period it reports on, the
filing date, and the exact URL it came from.

These are **public filings**, published by the U.S. Securities and Exchange
Commission on EDGAR (<https://www.sec.gov/edgar>) for anyone to read and
reuse. The companies wrote them, so they are not U.S. government works. We use
one section of each filing, unchanged, for teaching, and credit every source
above. Nothing here is investment advice, and nothing identifies a private
person.

The HTML is kept **exactly as EDGAR serves it**, apart from the cut: inline
styles, entities, page footers and all. Cleaning it is the project's third step.

`recorded/` and `questions.json` are ours: vectors made from this text by the
open `nomic-embed-text` model, a few model replies, and the labelled questions.
