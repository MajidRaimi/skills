---
name: prd-loop
description: Run a PRD.md (or one ROADMAP phase) on autopilot with the ralph-loop plugin. Makes sure the file has a checkbox task list and exact check commands, then starts a loop that builds one task per round, runs the checks, ticks it off and commits, until every task is done, with stuck tasks parked as blocked, a watchdog for silent stops, and a push notification at the end. Use when the user says "/prd-loop", "run the PRD", "autopilot the PRD", "loop until the PRD is done", "ralph this", "build phase 2", or asks to build everything in a PRD after a grill-me or product-docs session.
---

# PRD loop

Turns a finished PRD into an autopilot run. Each round of the loop re-reads the task file, picks the first open task, builds and checks it, ticks it and commits. The loop ends when every task is ticked or parked as blocked, or when it hits the round limit. Every ending sends a notification, and a watchdog reports a loop that stalls or dies silently.

Arguments (all optional): a PRD path (default `PRD.md`, then `docs/PRD.md`, then `docs/product/PRD.md`), `--phase N` to build one phase of `docs/product/ROADMAP.md`, `--max N` to override the round limit, and "just run it" to skip the go-ahead.

**Notifications (env var):** set `PRD_LOOP_NOTIFY_CMD` to a CLI that sends you push notifications and accepts a message, a `--kind` flag (`done`, `info`, `blocked`, `error`, `urgent`) and a `--title` flag, for example a wrapper around `ntfy publish` or your own notifier. Every notification call is guarded with `command -v`, so the skill works with no notifier configured; it just stays quiet. `scripts/watch.sh` uses the same mechanism.

## 1. Check the ground

- **Plugin:** `ls -d ~/.claude/plugins/cache/claude-plugins-official/ralph-loop/*/scripts/setup-ralph-loop.sh` must print a path. If not, tell the user to run `claude plugin install ralph-loop@claude-plugins-official` and stop.
- **Repo:** the folder must be a git repo. If it isn't, ask before running `git init`. Note the absolute repo root (`git rev-parse --show-toplevel`).
- **One loop per folder:** if `.claude/ralph-loop.local.md` already exists, a loop is running or died here. Ask before replacing it. For two loops at once, use a separate git worktree.
- **Working tree:** if there are uncommitted changes, ask whether to commit them first. Each round commits, so mixing in unrelated work is bad.
- **`.gitignore`** must contain `.claude/*.local.md`, `.claude/prd-loop.*`, `.env`, `.env.*` (keep `!.env.example`), `node_modules`, `.next`, `dist`, `build`, `.turbo`, `.venv` and `__pycache__`. Add the missing ones and commit before the loop starts.
- **Branch:** always create a new branch for this run, never reuse another phase's branch.
  - Phase runs: `feat/<slug>-phase-NN`, created from the previous phase's branch if it isn't merged yet, otherwise from the default branch.
  - Whole-PRD runs: `feat/<slug>`.
  - Say which base you used.
- **Task file:** if no PRD is found, stop and tell the user to run grill-me and `/product-docs` (or point at the file) first.

## 2. Make the task file

Decide which file the loop works on:
- **Small PRD** (40 tasks or fewer): the PRD itself.
- **`--phase N`, or a big PRD:** write `docs/build/phase-NN.md` with that phase's goal, scope, deliverables and exit criteria from `ROADMAP.md`, and link the spec sections it needs. One phase per loop. If it needs more than 40 tasks, split it into `phase-NNa.md` and `phase-NNb.md` and run them one after the other.

The task file must end with these sections:

```markdown
## Run
- Base: <commit sha before the loop started>
- Ports: web 3105, api 8105, postgres 5505 (free when checked with `ss -ltn`)

## Checks
- `bun run typecheck`
- `bun run lint`
- `bun run test` (enforced from T3, which adds the first test)
- `bun run build`

## Exit criteria
- `curl -fsS localhost:8105/health` returns 200
- Browser: sign up, create a project, see it in the list

## Tasks
- [ ] T1: Scaffold the API app with a health route. Needs: ARCHITECTURE.md#apps-api. Check: `curl -fsS localhost:8105/health` returns 200.
- [ ] T2: ...

## Blocked
```

Rules:
- **Base:** the output of `git rev-parse HEAD` at this moment. The review tasks diff against it.
- **Ports:** pick free ports with `ss -ltn` (or `lsof -iTCP -sTCP:LISTEN` on macOS), away from common defaults, and use them in `.env` and every check. Other projects' servers may run on this machine, so a default port can answer for the wrong app.
- **Checks:** the exact commands that must pass after every task, read from `package.json`, `turbo.json` or `pyproject.toml`. A check that a later task creates is marked "(enforced from Tn)" and is skipped until that task is ticked.
- **Exit criteria:** copied from the ROADMAP phase or derived from the PRD scope. Each must be runnable (a command, a URL, or a browser flow), never "works well".
- **Small tasks:** each fits in one round, about one feature slice or one screen.
- **Ordered:** setup and shared pieces first, then features in dependency order.
- **Needs:** each task names the spec sections it needs (`file#anchor`), so a round reads only those.
- **Check:** each task names its own check: a test, a URL, or a browser check for UI work.
- **Covers the scope:** every requirement in the PRD or phase maps to at least one task.
- **Env vars:** if a task needs a new env var, it adds it to `.env.example` with a working local default. Real secrets are listed under Blocked.
- **The last two tasks are always:**
  1. "Run /senior-review on `git diff <Base>..HEAD` and fix what it finds."
  2. "Adversarial check: run a fresh reviewer synchronously with `claude -p --permission-mode bypassPermissions "<brief>"` in Bash (never a background Agent). Brief it to hunt real regressions in `git diff <Base>..HEAD` and to run every exit criterion live. Fix what it finds."
- **Existing list:** if a `## Tasks` list already exists, keep it and its ticks. Only add missing tasks or split oversized ones.

Round limit: open tasks times 1.5, rounded up, plus 3 (or `--max`). Show the user the task list, exit criteria and limit, and wait for their go-ahead, because this is the last cheap point to change scope. Skip the wait if they said "just run it".

Commit the task file with `docs(build): add task list` (or `docs(build): add the phase N contract`).

## 3. Start the loop and the watchdog

Fill in `<REPO>` (absolute repo root), `<FILE>` (task file path relative to the repo) and `<PROJECT>` (short project name), then run:

```bash
rm -f "<REPO>/.claude/prd-loop.ended"
NOTIFY="${PRD_LOOP_NOTIFY_CMD:-}"
SETUP=$(ls -d ~/.claude/plugins/cache/claude-plugins-official/ralph-loop/*/scripts/setup-ralph-loop.sh | sort -V | tail -1)
cd "<REPO>" && "$SETUP" --completion-promise "PRD COMPLETE" --max-iterations <N> "$(cat <<'PROMPT'
You are building <FILE> in <REPO> on autopilot. One task per round. This loop is unattended: nobody will answer questions.

Start of round:
1. `cd <REPO>`. Read the ## Run, ## Checks, ## Exit criteria, ## Tasks and ## Blocked sections of <FILE>, `git status`, `git log --oneline -15`, and `head -8 .claude/ralph-loop.local.md` (iteration and max_iterations).
2. If the working tree is dirty, a previous round was interrupted: finish that task with those changes. If they are beyond repair, `git stash push -m "prd-loop leftovers"` (never discard work) and start the task again.

The task:
3. Take the first unticked task under ## Tasks that is not under ## Blocked. If it depends on a blocked task, move it under ## Blocked as "depends on T<n>" without trying it, and take the next one.
4. Read the spec sections the task names under "Needs" and build it following them and the repo's CLAUDE.md. Use only the ports listed under ## Run.
5. Run the task's own check and every enforced command under ## Checks. Fix until all pass. Never weaken, skip or delete a test, check or lint rule to make it pass.
6. Pass: tick it `[x]` and commit with a conventional message naming the task, for example `feat(auth): add login flow (T4)`. No Co-Authored-By line. Then check the Finish condition below in this same round.
7. Fail: if it still fails at the end of the round, append "(attempt N)" to the task line, commit as `wip: <task> (attempt N)`, and end the round. On the third failed attempt: `git branch wip/T<n>`, then `git reset --hard` to the last commit before this task's first wip commit, so later tasks start from green code. Then move the task under ## Blocked with the error, what you tried and the branch name, and commit that.
8. Needs a human (a product decision, a secret, an account, a payment, anything outward-facing): do not guess and do not ask. Put it under ## Blocked saying exactly what you need, then if $NOTIFY is set, call it as: $NOTIFY "<PROJECT>: T<n> blocked, <what you need>" --kind blocked (notifications are configured via the PRD_LOOP_NOTIFY_CMD env var; skip silently if unset or missing).

Never end a round while anything you started is still running: no background Agents or background shell jobs. Run subagents and reviewers synchronously (`claude -p` in Bash) and wait for their result, because the next round starts the moment this one ends.

Never, in any round: call AskUserQuestion, run interactive logins, push, merge, deploy, open PRs, delete branches, touch staging or prod, spend money, send messages or emails to anyone, edit files outside <REPO>, commit .env files or secrets, or kill processes you did not start.

End of round:
9. Stop any server or background process you started this round, by PID.
10. `cd <REPO>` as the last shell command, so the loop can find its state file.
11. If iteration equals max_iterations, this is the final round: `touch .claude/prd-loop.ended`, then if $NOTIFY is set: $NOTIFY "<PROJECT>: loop stopped at the round limit, <ticked> of <total> done, <blocked> blocked" --kind blocked.

Finish: the loop is finished when every task is ticked or under ## Blocked, every enforced check passes, every exit criterion passes when run live (unless a blocked task owns it), and `git status` is clean. Then `touch .claude/prd-loop.ended` and notify (only if $NOTIFY is set):
- ## Blocked is empty: $NOTIFY "<PROJECT>: <FILE> done, <ticked> tasks built, all exit criteria pass" --kind done.
- Otherwise: $NOTIFY "<PROJECT>: <FILE> finished with <blocked> blocked tasks, needs a human" --kind blocked.

Then end your message with exactly <promise>PRD COMPLETE</promise> as the final line, with no tool call after it. Never print that while an open task remains or a check or exit criterion fails.
PROMPT
)"
```

Then start the watchdog. It sends an error notification if the loop stalls (no new round or commit for 45 minutes, for example after an API error or a usage limit) or stops without finishing:

```bash
W=~/.claude/skills/prd-loop/scripts/watch.sh
if command -v systemd-run >/dev/null; then
  systemd-run --user --collect --unit "prd-loop-watch-<PROJECT>-$(date +%s)" bash "$W" "<REPO>" "<PROJECT>" 45
else
  nohup bash "$W" "<REPO>" "<PROJECT>" 45 >/dev/null 2>&1 &
fi
```

Then start round 1 right away by following the loop prompt.

**If round 2 never starts** (no "Ralph iteration 2" message), the plugin's stop hook isn't loaded in this session. The watchdog reports it within the hour. Tell the user to run `/reload-plugins` or start a new session and run `/prd-loop` again; the task file keeps all progress.

## While it runs

- **Progress:** `grep '^iteration:' .claude/ralph-loop.local.md`, the ticks in the task file, and `git log`.
- **Stop it:** `/cancel-ralph`, then `touch .claude/prd-loop.ended` so the watchdog stays quiet.
- **Don't `/clear` during a loop.** It starts a new conversation and the loop stops. Auto-compaction is fine.
- **Run it in its own session or terminal,** so other work isn't stuck behind it.

## When it ends

Report:
- tasks built, tasks blocked with what each needs, `wip/` branches, and any stashes left behind;
- the branch and its base, the final check and exit-criteria results, and the senior-review and adversarial-check outcomes;
- the next phase to run, if any.

Don't push or open a PR unless the user asks.
