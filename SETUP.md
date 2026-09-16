# Setup — do this before September 14

Work through this list top to bottom. At the end, one command prints a green
checklist; screenshot it and post it in the cohort channel. Budget ~30 minutes.

## 0. Which terminal you will be typing into

Every command in this course is written for a **Unix-style shell**. Pick yours
now, because a command pasted into the wrong one fails on its first line and
the error will not tell you why.

| | Use | Open it with |
|---|---|---|
| **macOS** | Terminal | Spotlight → "Terminal" |
| **Linux** | your terminal | you already know |
| **Windows** | **Git Bash**, or WSL2 | Git Bash ships with git, below. For WSL2: `wsl --install` in PowerShell, once, then use the Ubuntu terminal |

**Windows, in one line:** PowerShell works for installing uv and nothing else
here. Use **Git Bash** for the rest, or **WSL2** if you would rather have a
full Linux. Both are free, both take minutes, and both remove a whole class of
error you would otherwise spend the week on.

Everything after this assumes you are in that shell.

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

## 3. Install git

git is how you get the course and how you hand work in. Most machines already
have it — check first:

```bash
git --version
```

If that prints a version, skip ahead. If it says *command not found*:

| | |
|---|---|
| **macOS** | `xcode-select --install`, or install from <https://git-scm.com/downloads> |
| **Windows** | <https://git-scm.com/downloads> — accept every default. This also gives you **Git Bash**, which is the terminal to use for every command in this course |
| **Linux** | `sudo apt install git` (Debian/Ubuntu) or `sudo dnf install git` (Fedora) |

You also need a **GitHub account**, because your submissions are pull requests
from your own fork: <https://github.com/signup>. A pseudonymous account is
fine; nothing in this course needs your real name.

## 4. Clone the course

The repository is **public** — there is nothing to request and nothing to wait
for.

```bash
git clone https://github.com/Gecko-Academy/dev3pack-cohort-2026-09.git
cd dev3pack-cohort-2026-09
```

That `cd` matters more than it looks: **every command below is run from inside
that directory.** Running them anywhere else is the most common cause of
`bootcamp: command not found`.

(If you have SSH keys set up, `git clone git@github.com:Gecko-Academy/dev3pack-cohort-2026-09.git` works too.)

**The repository grows each week.** Week 0, the prerequisite, is there now.
Week 1 appears on Monday 14 September, week 2 on the 21st, week 3 on the 28th.
Run `git pull` at the start of each week to get it. Nothing you have written is touched by a pull, because you never push to this
repository — see *Saving your own work* below.

## 5. Install it and check it works

```bash
uv run bootcamp start
```

That is the whole of steps 5 and 6. It is safe to run as many times as you
like — every step checks before it acts — and it ends by naming the one command
to run next.

The rest of this section is what it does, for when you want to do a piece by
hand or something went wrong in the middle.

**The install.**

```bash
uv sync --group dev
cp .env.example .env
```

**macOS only, and it bites before anything can tell you why.** uv marks what it
installs into `.venv` as hidden, and Python skips a hidden `.pth` file —
including the one that makes `bootcamp_agent` importable. Every command then
fails with `ModuleNotFoundError: No module named 'bootcamp_agent'` on a machine
where nothing is actually wrong.

`uv run bootcamp doctor` repairs it automatically every time it runs. To do it
by hand:

```bash
chflags -R nohidden .venv
```

`uv sync` creates `.venv/` and installs everything, including the dev tools
(pytest, ruff, notebook tooling). You never activate the venv by hand — always
prefix commands with `uv run`.

**The check.**

```bash
uv run bootcamp doctor
```

It checks Python, the kernel, the teaching corpus and the offline model lane,
and tells you what to run for anything missing. A green doctor is the whole bar
for starting.

(There is no `pytest` step here. The test suite is ours, not yours -- it holds
the solved value of every exercise, so it is not in your copy. Running it finds
nothing and says so in a way that reads like a broken install.)

Everything green (⚠️ warnings are fine)? **Screenshot the doctor output and post
it in the cohort channel.** That's your ticket for day 1.

Then open the course and find your place:

```bash
uv run jupyter lab      # then open 00-START-HERE.ipynb, the first file listed
```

That notebook lists every part of the course in order, links each one, and ticks
off what you have finished. Week 0 is open now, so you can begin the moment the
doctor is green.

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
| Ollama (local, free, no key; wants ~8 GB of RAM free) | Install from <https://ollama.com>, then `ollama pull qwen2.5:7b-instruct` → in `.env`: `BOOTCAMP_PROVIDER=ollama`. Nothing else to install. The doctor checks the server and the model. |
| Anthropic | Get a key at <https://console.anthropic.com> → in `.env`: `BOOTCAMP_PROVIDER=anthropic`, `ANTHROPIC_API_KEY=...` and `uv sync --extra anthropic` |
| OpenRouter (one key, many models, has free models) | Key at <https://openrouter.ai> → `BOOTCAMP_PROVIDER=openai`, `OPENAI_API_KEY=...`, `OPENAI_BASE_URL=https://openrouter.ai/api/v1` and `uv sync --extra openai` |
| OpenAI | Key at <https://platform.openai.com> → `BOOTCAMP_PROVIDER=openai`, `OPENAI_API_KEY=...` and `uv sync --extra openai` |

Then: `uv run bootcamp-agent "How does chunking work in RAG?"`

### A Claude Pro or Max subscription does not pay for an API key

This one has cost people money, so read it twice. A subscription and the API
are **two separate products with two separate bills**:

| | What it covers | What it costs |
|---|---|---|
| **Claude Pro / Max** | Claude on the web, and **Claude Code** | your monthly subscription, nothing more |
| **An API key** from <https://console.anthropic.com> | the `anthropic` lane above | **billed per token, separately**, on top of any subscription |

Anthropic's own documentation puts it plainly: *"Claude Code requires a Pro,
Max, Team, Enterprise, or Console account."* So if you have Pro, **Claude Code
is already paid for** — and Claude Code is exactly what sessions 1 and 10 ask
for. Creating an API key does not draw on that subscription; it opens a
metered account.

The same is true everywhere: a ChatGPT Plus subscription does not pay for an
OpenAI API key either.

**And none of this is required.** Every scored notebook in this course runs on
the `fake` lane with no key, no account and no network. If you want a real
model, **Ollama is free and local** — that is the first row for a reason.

**Never commit `.env`. Never paste a key into a prompt, an issue, or a config
file that gets committed.**

### If 8 GB is all you have: run the model on Colab instead

Do not fight your laptop. Google Colab is free, needs no card, and gives you more
memory than your machine plus a GPU — and the model runs *there*, so nothing is
installed locally.

**[demos/04_ollama_on_colab.ipynb](demos/04_ollama_on_colab.ipynb)**

Open it in Colab, set **Runtime → Change runtime type → T4 GPU** *first*, then run
the cells in order. It installs Ollama there, pulls `qwen2.5:7b-instruct`, and
points the course at it.

One measured warning, so you do not lose an evening to it: **a 1B model cannot do
session 3.** It fails to produce a valid `confidence`, twice, and the parser
refuses it — correctly. Use the 7B.

The cost of this route is that Colab forgets: a new machine means pulling the
model again, about three minutes. Your submissions still happen on your own
laptop, because `bootcamp submit` needs your checkout.

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
| **`bootcamp: command not found`** | The two causes, in order of likelihood. **One:** you are not inside the course folder — run `pwd`, and `cd dev3pack-cohort-2026-09` if it is missing from the path. **Two:** you dropped the prefix — it is `uv run bootcamp doctor`, never `bootcamp doctor` |
| `No such file or directory: pyproject.toml` | Same cause as above: wrong directory |
| A command is not found | You ran it bare — everything is prefixed `uv run` |
| Doctor says corpus missing | You're not in the repo root — `cd` into the cloned folder |
| `Permission denied (publickey)` or `Repository not found` when cloning | The repository is public, so this is an SSH key problem, not an access one. Clone over HTTPS instead: `git clone https://github.com/Gecko-Academy/dev3pack-cohort-2026-09.git` |
| `ModuleNotFoundError: No module named 'bootcamp_agent'` on macOS | uv hid `.venv`'s `.pth` files on the last `uv sync`. `uv run bootcamp doctor` clears it, or `chflags -R nohidden .venv` |
| Next week's folder is not there after `git pull` | It has not been published yet. Each week appears on its Monday |

Stuck longer than 15 minutes? Post the doctor output (never your `.env`) in the
cohort channel.
