---
name: product-docs
description: Turn a finished grill-me session into a full product documentation set. Writes docs/product/DECISIONS.md from the conversation, has the user confirm it, then writes PRD, PRODUCT.md and DESIGN.md (impeccable), architecture, AI engine, security, data model, API, billing and roadmap specs with parallel subagents, then runs a skeptical cross-document review, settles the open decisions with them, and checks the result mechanically. Use when the user says "/product-docs", "generate the docs", "write the PRD and everything", "create all the documents", "PRD.md, DESIGN.md etc", or finishes a grill-me or mcq session about a product and wants it written down.
---

# Product docs

Writes the whole spec set for a product from what was decided in a grill-me session. Every document is derived from one file, `docs/product/DECISIONS.md`, which wins on any conflict.

Arguments (optional): extra notes, documents to skip or add ("no billing", "add MOBILE.md"), and "just write it" to skip the confirmation gates.

**Why the order matters:** a mistake in `DECISIONS.md` gets copied into thousands of lines across ten documents. So the decisions are recovered carefully, confirmed by the user, and given a shared vocabulary before any writer starts.

## 0. Before you start

- **There must be decisions to write down.** If the grill happened in another session, find its transcript with `grep -l '<product name>' ~/.claude/projects/*/*.jsonl` (newest first) or ask the user which session it was, and recover the answers from it. If there was no grill at all, run grill-me first (with AskUserQuestion if the user asked for mcq). Don't start writing until the user says the grilling is done.
- **Coverage check:** the grill should have touched each of these areas. List the ones it didn't; they become Default rows that the user confirms at step 1.
  1. Product scope, users, and what v1 does not do
  2. Organizations, roles and access
  3. Money: plans, trial, payment and invoicing providers (or "free")
  4. Every v1 feature
  5. Architecture: apps, services, data stores, AI models
  6. Hosting, data residency, compliance
  7. Languages and RTL
  8. Delivery: first milestone, what "done" means
- **Repo:**
  - In a git repo, create `docs/product-spec` from the default branch.
  - For a brand new product with no repo, ask where it belongs (folder names lowercase). Then `git init -b main` with a README and `.gitignore`, commit, and create `docs/product-spec`. Create the remote only if the user says so.
  - Agents never commit, push or switch branches; you commit at the end.
- **Read the project:** the README, any existing code (landing pages, schemas, `package.json`, `docker-compose.yml`, `mprocs.yaml`) and research notes in `docs/`.

## 1. Write and confirm DECISIONS.md

You write `docs/product/DECISIONS.md` yourself, before any agent starts, because only you have the conversation.

- **Recover the answers exactly.** If the grill was long or this session was compacted, read the session transcript (`~/.claude/projects/<project-dir>/<session-id>.jsonl`). AskUserQuestion answers are in its tool results, and the user's typed replies are in the user messages. Don't rebuild them from memory or a summary.
- **Header:** "The record of the product grill session on <date> between the product owner and Claude. Every other document in `docs/` is derived from this file. When a later document disagrees with this file, this file wins until it is updated."
- **Status per decision:** **Decided** (the user chose it) or **Default** (not asked, your recommended default, open to change).
- **Sections,** each a `| Topic | Decision | Status |` table:
  1. Product scope (including what v1 does not do)
  2. Organizations, users and access
  3. Billing
  4. Features (v1)
  5. Architecture
  6. Delivery

  Drop a section that doesn't apply.
- **Section 0, Vocabulary**, at the top. This is the shared contract that keeps parallel writers consistent:
  - the product name in every language and its domains and subdomains;
  - the app and service names (`apps/web`, `apps/api`, ...);
  - role names;
  - core entity names;
  - status enums (for example finding, job and subscription states);
  - plan names;
  - real-time channel naming, if any.

  Mark entries the user didn't choose as Default.
- **No invented numbers:** never invent prices, quotas or targets; use named placeholders such as `PLAN_TEAM_SEAT_MONTHLY`.
- **Confirmation gate:** show the user every Default row and every coverage gap from step 0 as AskUserQuestion rounds (up to 4 questions each, your recommendation first). Update the rows they change to Decided. Skip only if the user said "just write it", and then say how many Defaults went unconfirmed.

Commit `DECISIONS.md` alone (`docs(product): record product decisions`), so later edits to it are easy to see.

## 2. Pick the document set

| File | Write it when |
|---|---|
| `docs/product/PRD.md` | always |
| `PRODUCT.md` and `DESIGN.md` (repo root, impeccable format) | the product has any UI |
| `docs/product/ARCHITECTURE.md` | always |
| `docs/product/AI-ENGINE.md` | the product has AI or agent features |
| `docs/product/SECURITY.md` | always |
| `docs/product/DATA-MODEL.md` and `docs/product/API.md` | there is a backend or database |
| `docs/product/BILLING.md` | it charges money |
| `docs/product/ROADMAP.md` | always |
| `docs/product/REVIEW-NOTES.md` | always (written by the review in step 4) |

Tell the user the set in one line and go, unless they asked to choose.

**Dependencies:** the `impeccable` and `to-spec` skills must be installed alongside this one. Check that they exist under the user's skills directory (for example `~/.claude/skills/impeccable` and `~/.claude/skills/to-spec`). If one is missing, its brief falls back to the structure written in the brief itself; say so in the report.

## 3. Write in parallel

Start one background Agent per group below, all in the same message. Each agent owns only its files. Build each prompt from [references/briefs.md](references/briefs.md): the shared rules plus that group's brief, with the real repo path, product name and sources filled in. Before sending, make sure no `<REPO>`, `<PRODUCT>`, `<DATE>` or `<SOURCES>` placeholder is left in any prompt.

1. `PRD.md`
2. `PRODUCT.md` and `DESIGN.md` (through the impeccable skill)
3. `ARCHITECTURE.md`, `AI-ENGINE.md`, `SECURITY.md`
4. `DATA-MODEL.md`, `API.md`
5. `BILLING.md`, `ROADMAP.md`

Skip groups or files that step 2 dropped. Tell the user which agents are writing what. When they finish:
- confirm every expected file exists and isn't a stub (`wc -l`);
- re-run any agent that failed or stopped early with the same brief;
- if an agent reports that DECISIONS.md itself needs a change, collect it for step 5. Never let agents edit it.

## 4. Review across the documents

When all writers are done, start a fresh Agent with the review brief from [references/briefs.md](references/briefs.md).
- **Large sets:** if the documents total more than about 9,000 lines, split it into two reviewers that run one after the other: first the DECISIONS coverage and house rules, then the cross-document names, endpoints and enums. Running them in parallel would mean two agents editing the same files.
- **What it produces:** it fixes contradictions in place, and writes `REVIEW-NOTES.md` with a coverage table (each Decided row and where it lands) and the decisions that need the user, each with a recommended answer.

## 5. Settle the open decisions

- Ask the user the `REVIEW-NOTES.md` section 3 decisions, plus any DECISIONS.md changes the agents proposed, with AskUserQuestion (your recommendation first, up to 4 per round).
- Add their answers to `DECISIONS.md` as a new section "7. Review follow-ups (<date>)".
- Start one Agent with the propagate brief to apply that section to every document and mark those items resolved in `REVIEW-NOTES.md`.
- Skip this step if the user said "just write it". The proposals then stay open in `REVIEW-NOTES.md`.

## 6. Check and finish

- **Mechanical check:** run `uv run --no-project python -I <this skill's directory>/scripts/check_docs.py <repo>` (resolve `<this skill's directory>` to wherever this skill is installed, for example `~/.claude/skills/product-docs`).
  - **Errors** fail the check: em or en dashes, broken relative links, leftover template placeholders, unclosed code fences. Fix them all and run it again until it exits 0.
  - **Warnings** to look at: money amounts (make sure each one is a real decided figure or a unit note, not an invented price), and documents that never name `DECISIONS.md`.
- **Coverage:** every v1 feature in the PRD appears in a ROADMAP phase, and every Decided row appears in the coverage table.
- **Commit:** `docs(product): add PRD, product, design, architecture, ... specs` (name what was written). Push and open a PR only if the user asks.
- **Report:**
  - a table of the files with line counts and one line on each;
  - the decisions still open, and how many Defaults the user never confirmed;
  - the next step: `/prd-loop docs/product/ROADMAP.md --phase 0` (one phase per loop), after the docs branch is merged or by branching from it.

## Rules

- `DECISIONS.md` is written only by you, from the user's words. Agents never edit it; they list the changes they need in their report.
- No em dashes or en dashes anywhere. No code comments in code samples.
- Anything not in `DECISIONS.md` is marked "Assumption:". Unsourced claims about third-party services are marked "Unverified:". Research claims cite URLs.
- No invented numbers presented as real, and no certification or compliance claims the product doesn't have.
- The architecture follows the user's own engineering rules (read them from `~/.claude/CLAUDE.md` if present). The default house style: feature-first layout, a Turborepo monorepo with mprocs, Bun and uv as package managers, docker compose plus `.env.example` for every service, and an env-var manager for secrets.
