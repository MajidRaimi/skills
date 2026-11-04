# Majid Raimi's Claude Code skills

A curated collection of Claude Code skills I built for my own daily work, scrubbed of my personal infrastructure, credentials, and client references so anyone can install and use them.

Every skill here is something I wrote myself and use. Credentials that were hardcoded in my private copies are replaced by environment variables, which each affected skill documents in a Configuration section.

## What's inside

| Skill | One line | Env vars it expects |
|---|---|---|
| prd-loop | Runs a PRD or task file on autopilot with the ralph-loop plugin, ticking, checking and committing one task per round | `PRD_LOOP_NOTIFY_CMD` (optional notifier CLI) |
| product-docs | Turns a grill-me conversation into a full product spec set (PRD, PRODUCT, DESIGN, architecture, security, data model, API, billing, roadmap) | none |
| security-audit | Adversarial security review: attack classes, hunting protocol, data isolation, supply-chain and RPC guides, report schema with validators | none |
| grill-me | Interviews you relentlessly about a plan until every decision branch is resolved | none |
| handoff | Reviews a session end-to-end and produces the close-out summary plus next-step plan | none |
| mcq | Answers your questions as multiple-choice cards via the AskUserQuestion tool | none |
| nextjs-patterns | Full architecture rules for Next.js App Router projects (Zustand, TanStack Query with hydration, nuqs, react-hook-form, zod, mprocs, Infisical) | none |
| find-skills | Discovers and installs new skills from community repos when you ask "how do I X" | none |
| design-md | Brand design-system generator with a library of brand specs (Nike, Starbucks, Replicate and more) | none |
| sync-env | Keeps local .env files in sync with a self-hosted Infisical instance | `INFISICAL_DOMAIN` (required), `INFISICAL_TOKEN` (optional) |
| ntfy-me | Sends a push notification to your own ntfy server, on your own topic, with your session as the title | `NTFY_HOST`, `NTFY_TOPIC`, `NTFY_TOKEN` (plus the optional `NTFY_CLICK_URL`, `NTFY_TITLE`, `NTFY_TITLE_FALLBACK`) |
| call-me | Phones the owner via Bland.ai when blocked on a decision, asks the question, waits for the call, and continues with the answer | `OWNER_PHONE` (E.164), `BLAND_API_KEY` (plus optional `BLAND_ENCRYPTED_KEY`, `CALL_ME_FROM`, `CALL_ME_VOICE`, `OWNER_NAME`, `CALL_ME_FIRST_SENTENCE`) |

## Install

Any of these installs for any agent that reads Claude Code skill directories (Claude Code, Codex, OpenCode, Pi):

```bash
git clone https://github.com/MajidRaimi/skills ~/.agents/skills
# or link a single skill into Claude Code only:
ln -s ~/.agents/skills/<name> ~/.claude/skills/<name>
```

Or pick one skill:

```bash
curl -fsSL https://raw.githubusercontent.com/MajidRaimi/skills/main/skills/<name>/SKILL.md -o ~/.claude/skills/<name>/SKILL.md
# then copy any scripts/references the skill ships with: rsync -a skills/<name>/ ~/.claude/skills/<name>/
```

For Claude Code plugin-style install (the way obra/superpowers works), the layout matches: each directory under `skills/` is a self-contained skill with its own `SKILL.md`.

## Configuration

Skills that expect env vars each document them in their own `SKILL.md` under a Configuration section, with a fake example value. Set them in your shell profile or where you launch the agent:

```bash
export INFISICAL_DOMAIN=https://infisical.example.com
export NTFY_HOST=https://ntfy.example.com
export NTFY_TOPIC=you
export NTFY_TOKEN=tk_...
export OWNER_PHONE=+1555000123
export BLAND_API_KEY=sk-bland-...
```

## Provenance

The 12 skills in this repo were written by me for my own use. Third-party skills I use privately (like mattpocock/to-spec, Matt Paquette's excellent public packs) are deliberately not bundled; credit where credit is due, and this repo carries only my original work.

## License

MIT, see [LICENSE](LICENSE).
