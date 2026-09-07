# Setup — do this before September 14

Work through this list top to bottom. At the end, one command prints a green
checklist; screenshot it and post it in the cohort channel. Budget ~30 minutes.

## 1. Install uv

uv manages Python versions, virtual environments, and dependencies — it is the
only installer this course uses.

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify: `uv --version` (0.4+ is fine).

## 2. Install Python 3.11+

```bash
uv python install 3.11
```

(If you already have 3.11+ on your system, uv will find it — this step is then a no-op.)

## 3. Get access, then clone the repository

The course repository is **private**. Before you can clone it, you need an
invitation, and the invitation goes to a GitHub account.

1. **Send us the email address on your GitHub account.** Not any email — the one
   GitHub knows, or the invitation will not reach you. It is under
   <https://github.com/settings/emails>. If you have no GitHub account yet,
   create one first: <https://github.com/signup>.
2. **Accept the invitation.** It arrives by email and also appears at
   <https://github.com/notifications>. It expires after seven days.
3. **Then clone.**

git: <https://git-scm.com/downloads> (already present on most systems — `git --version`).

```bash
git clone git@github.com:Gecko-Academy/dev3pack-cohort-2026-09.git
cd dev3pack-cohort-2026-09
```

(HTTPS also works: `git clone https://github.com/Gecko-Academy/dev3pack-cohort-2026-09.git`)

**The repository grows each week.** Week 0, the prerequisite, is there now.
Week 1 appears on Monday 14 September, week 2 on the 21st, week 3 on the 28th.
Run `git pull` at the start of each week to get it. Nothing you have written is touched by a pull, because you never push to this
repository — see *Saving your own work* below.

## 4. Install the project

```bash
uv sync --group dev
cp .env.example .env
```

`uv sync` creates `.venv/` and installs everything, including the dev tools
(pytest, ruff, notebook tooling). You never activate the venv by hand — always
prefix commands with `uv run`.

## 5. Run the tests and the doctor

```bash
uv run pytest -q
uv run python scripts/check_setup.py
```

Everything green (⚠️ warnings are fine)? **Screenshot the doctor output and post
it in the cohort channel.** That's your ticket for day 1.

## 6. Install an editor and ONE coding assistant

Any of these works for the course — Session 4 covers configuring them properly:

| Assistant | Install |
|---|---|
| Claude Code (CLI) | `npm install -g @anthropic-ai/claude-code` then `claude` |
| Cursor | <https://cursor.com/download> |
| Codex CLI | `npm install -g @openai/codex` |

You need a working login for whichever one you pick (free tiers are fine for the
exercises). VS Code or PyCharm as the editor is your choice.

## 7. (Optional, can wait) A real model for live calls

The course runs offline by default on the FakeLLM. When you want real model
answers, pick ONE. The first row needs no key and no account.

| Provider | Setup |
|---|---|
| Ollama (local, free, no key; needs 8 GB RAM) | Install from <https://ollama.com>, then `ollama pull qwen2.5:7b-instruct` → in `.env`: `BOOTCAMP_PROVIDER=ollama`. Nothing else to install. The doctor checks the server and the model. |
| Anthropic | Get a key at <https://console.anthropic.com> → in `.env`: `BOOTCAMP_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...` and `uv sync --extra anthropic` |
| OpenRouter (one key, many models, has free models) | Key at <https://openrouter.ai> → `BOOTCAMP_PROVIDER=openai`, `OPENAI_API_KEY=...`, `OPENAI_BASE_URL=https://openrouter.ai/api/v1` and `uv sync --extra openai` |
| OpenAI | Key at <https://platform.openai.com> → `BOOTCAMP_PROVIDER=openai`, `OPENAI_API_KEY=...` and `uv sync --extra openai` |

Then: `uv run bootcamp-agent "How does chunking work in RAG?"`

**Never commit `.env`. Never paste a key into a prompt, an issue, or a config
file that gets committed.**

## Saving your own work

You have **read access**, which is deliberate: it means nothing you do can break
the course for the rest of the cohort. You will not be able to `git push`, and
you do not need to.

Your notebook edits live on your own machine. If you want them backed up or
shared, make your own repository and add it as a second remote:

```bash
git remote add mine git@github.com:<your-username>/<your-repo>.git
git push mine main
```

`git pull` (from `origin`) still brings you each new week.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `uv: command not found` after install | Restart the terminal; on macOS/Linux ensure `~/.local/bin` is on PATH |
| Corporate proxy blocks installs | `export UV_HTTP_TIMEOUT=120` and configure `HTTPS_PROXY`; worst case use a personal network for setup |
| `python` is 3.9/3.10 | Irrelevant — `uv run` uses the project's own 3.11; don't fight the system Python |
| Windows: `ExecutionPolicy` error | Run PowerShell as administrator once for the installer, or use WSL2 (recommended) |
| `pytest` not found | You ran it bare — always `uv run pytest` |
| Doctor says corpus missing | You're not in the repo root — `cd` into the cloned folder |
| `Permission denied (publickey)` or `Repository not found` when cloning | You have not accepted the invitation yet, or you accepted it with a different GitHub account. Check <https://github.com/notifications>, then step 3 above |
| `git pull` says `Permission denied` | Same cause. Read access is per-account, and SSH keys are per-machine — add this machine's key at <https://github.com/settings/keys>, or clone over HTTPS |
| Next week's folder is not there after `git pull` | It has not been published yet. Each week appears on its Monday |

Stuck longer than 15 minutes? Post the doctor output (never your `.env`) in the
cohort channel.
