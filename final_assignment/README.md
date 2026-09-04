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

# Final Assignment — earn the certificate

The bootcamp ends the Hugging Face way: a template you make your own, a
question set your agent is graded on, and a certificate when you pass.

## How it works

1. **Build your agent** in [`agent.py`](agent.py). The template ships wired to
   the bootcamp package with the offline `FakeLLM` — as shipped it scores 30%
   (the refusal questions pass; the grounded ones don't). That is the
   point: like the course itself, the default answer is honest and
   insufficient. Improve it: configure a real provider (`.env`,
   `BOOTCAMP_PROVIDER`), tune retrieval, extend the corpus handling — anything,
   as long as the capstone contract holds (citations verified, refusal on
   unsupported questions, bounded tools).
2. **Grade yourself** against the public practice set, as many times as you
   like:

   ```bash
   uv run python final_assignment/grade.py --name "Your Name"
   ```

   This prints the per-question table and writes `score_report.json`. Pass bar:
   **70%**.
3. **Final grading** happens at demo day: the instructor runs the same grader
   with a **private question set** (same JSONL format, unseen questions — same
   distribution: grounded, refusal, adversarial). Your practice score is for
   you; the private-set score is what counts.
4. **The certificate** is issued by the instructor for a passing private-set
   score plus a completed demo (Session 15's demo contract). It carries an
   HMAC verification code only the instructor can produce:

   ```bash
   # instructor only (CERT_SIGNING_SECRET set):
   uv run python final_assignment/certificate.py --report score_report.json --out certificate.svg
   # verification (recomputes the HMAC, so it also needs the course secret):
   uv run python final_assignment/certificate.py --verify certificate.svg
   ```

   Without the secret the script still runs, but the output is watermarked
   **PREVIEW — NOT VERIFIED** (useful for checking your layout, useless for
   claiming a pass).

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
your agent answer with citations — and refuse without them.

**Never put an API key in the Space repo.** Use the Space's Settings → Secrets
for provider keys; locally they live only in `.env`.

## Files

| File | What it is |
|---|---|
| `agent.py` | **Yours.** The agent the grader runs — edit this. |
| `questions.jsonl` | The public practice set (10 questions). |
| `grade.py` | The grader — same pass logic as the course evals. |
| `certificate.py` | Certificate generator + verifier (instructor signs). |
| `app.py` | Gradio UI for the Space version. |
| `requirements.txt` | Space-only dependencies. |

## What the grader checks

Exactly what the course taught, nothing else:

- **Grounded questions** pass when every expected doc id appears in your
  answer's citations and the answer is not flagged for human review.
- **Refusal questions** pass when your agent flags human review and cites
  nothing — refusing well is scored, not penalized.
- **Adversarial phrasings** pass on the same rules; instructions embedded in
  questions must be quoted or ignored, never obeyed.
