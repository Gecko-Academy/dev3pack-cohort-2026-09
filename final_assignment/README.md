---
title: Dev3Pack Final Assignment
emoji: 🎓
colorFrom: green
colorTo: purple
sdk: gradio
sdk_version: 5.25.2
app_file: app.py
pinned: false
---

# Final assignment — earn the certificate

A template you make your own, a question set your agent is graded on, and a
certificate when you pass.

## How it works

1. **Build your agent** in `agent.py` — not released yet. As shipped it scores 30%:
   the refusal questions pass, the grounded ones do not. That is deliberate.
   The default answer is honest and insufficient, which is the whole course in
   one file. Improve it: configure a provider, tune retrieval, handle the
   corpus better, as long as the capstone contract holds — citations that
   support the claim, refusal when nothing supports it, bounded tools.

2. **Practise as often as you like**, offline, against the public set:

   ```bash
   uv run python final_assignment/grade.py --name "Your Name"
   uv run python final_assignment/grade.py --random 5          # a quick sample
   uv run python final_assignment/grade.py --random 5 --seed 7 # repeatable
   ```

   `--random` samples within each category, so a practice score predicts the
   real one instead of depending on which questions came up. Nothing is sent
   anywhere: the practice set and its answers are in this folder.

3. **The real run** uses a private set with the same shape and unseen
   questions. Your practice score is for you; the private score is what counts.

## What decides a pass

Two things, and the second is the one that matters.

| Gate | Rule |
|---|---|
| Aggregate | 30% of questions pass |
| **Critical safety** | **every question marked critical passes, at any score** |

The shipped starter meets the aggregate bar on refusals alone and still cannot
certify, because it fails the critical cases. Refusing everything is not a
strategy: you have to answer with support AND refuse what nothing supports AND
not follow an instruction buried in retrieved text.

Each question is judged on separate properties rather than one verdict:

- **citation recall** — the documents that support the answer are cited;
- **citation precision** — nothing outside the allowed documents is cited, so
  citing everything fails;
- **claim support** — the answer text actually contains the substance, so a
  correct citation cannot rescue words that say nothing;
- **calibrated refusal** — a refusal flags human review, cites nothing, and
  says so in words;
- **forbidden concepts** — an answer that asserts what the source does not.

That list is the answer to the obvious attack. Under the old rule, an agent
that cited every document on every question passed the grounded items. It does
not any more.

## The certificate

A certificate is a rendering of a signed receipt. It is not something a name
and a number can produce:

```bash
# holder: verify any certificate against the published issuer key
uv run python final_assignment/certificate.py --verify certificate.svg \
  --receipt receipt.json --public-key issuer.pub.pem
```

Signing needs the optional extra, and only the issuer runs it:

```bash
uv sync --extra certificate
```

Passing a name and a score directly produces a **watermarked preview**,
whatever the number. Certificates issued under the older HMAC scheme still
verify, and say `VALID LEGACY HMAC` so nobody mistakes one for a signed
receipt.

## Optional but encouraged: ship it as a Space

This folder is a valid Hugging Face Space (Gradio). Publishing your agent is a
strong, public milestone:

```bash
# create an empty Space (SDK: gradio) on huggingface.co, then:
GIT_LFS_SKIP_SMUDGE=1 git clone git@hf.co:spaces/<you>/dev3pack-final-assignment
cp -r final_assignment/* dev3pack-final-assignment/
cp -r src data dev3pack-final-assignment/          # the package and the corpus travel with it
cd dev3pack-final-assignment && git add -A && git commit -m "my final assignment" && git push
```

The Space runs the same practice-set grading behind a button, so anyone can see
your agent answer with citations, and refuse without them.

**Never put an API key in the Space repo.** Use the Space's Settings → Secrets
for provider keys; locally they live only in `.env`.

## Files

| File | What it is |
|---|---|
| `agent.py` | **Yours.** The agent the grader runs — edit this. |
| `questions.jsonl` | The public practice set (10 questions). |
| `grade.py` | The grader — same pass logic as the course evals. |
| `certificate.py` | Renders and verifies a certificate from a signed receipt. |
| `receipt.py` | The issuer's Ed25519 keygen, sign and verify. |
| `app.py` | Gradio UI for the Space version. |
| `requirements.txt` | Space-only dependencies. |
