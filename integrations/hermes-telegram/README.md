# Hermes × Telegram — your agent in your pocket

[Hermes](https://github.com/NousResearch/hermes-agent) is Nous Research's
self-improving agent framework; its gateway process speaks Telegram (plus
Discord, Slack, WhatsApp, Signal, and a local CLI) — one agent, reachable from
any device, with voice notes auto-transcribed and scheduled tasks reporting
back into the chat.

This integration is a **guided setup**, not a bundled dependency: Hermes is its
own uv-managed installation, and Telegram needs a bot token only you can
create. The checker script below verifies each step and tells you the next one.

## 1. Install Hermes (uv-based, like this course)

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

(Read the script first if that's your policy — it installs uv + Python 3.11
and clones the repo; no sudo.)

## 2. Create the Telegram bot

1. Open Telegram, talk to **@BotFather** → `/newbot` → pick a name and handle.
2. Copy the token BotFather gives you into `.env` (NEVER into git):

```bash
echo 'TELEGRAM_BOT_TOKEN=123456:ABC-your-token' >> .env
```

## 3. Configure + run the gateway

Follow the [Telegram guide](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram)
to point Hermes at your token, then start the gateway and message your bot.
Hermes also needs an LLM provider key (it supports several — your OpenRouter
key from `SETUP.md` works).

## 4. Verify

```bash
uv run python integrations/hermes-telegram/check_hermes.py
```

Prints a ✅/⚠️ checklist: hermes installed, token present, provider key
present — and the exact next command when something's missing.

## Try these once it's chatting

- Ask it a bootcamp-corpus question, then the same one via
  `uv run bootcamp-agent --trace` — compare what a *self-improving general
  agent* does vs your *bounded, citation-verified* one. Both behaviors are
  correct; they're built for different trust models.
- Give it a small repeated task for a week and watch the skill it distills —
  then read the skill file it wrote and review it like you reviewed a
  colleague's `SKILL.md` in Session 10.

## The course's safety lens (read before you run it long-term)

Hermes's superpower — persistent memory that shapes future behavior — is also
a **persistent injection surface** (Sessions 11 and 14). House rules:

- The bot token and provider keys live in `.env`/config, never in git.
- Don't point a self-improving agent at group chats with strangers while it
  has any capable tools attached; content it reads becomes behavior it keeps.
- "It got better" is a measurable claim: keep a small golden set of tasks and
  rerun it weekly (Session 9). Self-improvement without an eval is drift.
