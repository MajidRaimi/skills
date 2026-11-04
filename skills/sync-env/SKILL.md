---
name: sync-env
description: >
  Sync local .env files with a self-hosted Infisical instance, where Infisical is the
  source of truth for environment variables across machines. Project = GitHub repo name
  (bound via committed .infisical.json); apps/<name>/.env maps to Infisical folder /<name>.
  Bootstraps the Infisical CLI (install if missing) and login on any machine before syncing.
  Use when the user says "sync env", "update env", "pull env", "push env", "pull secrets",
  "env vars missing", "set up env on this machine", "infisical sync", or invokes /sync-env.
  Also use after editing any local .env to mirror the change up to Infisical.
license: MIT
---

# /sync-env: Infisical env sync

Keep each repo's local `.env` files in sync with a self-hosted Infisical instance, the
cross-machine source of truth. All real work lives in the bundled script; invoke it rather than
reimplementing the logic.

## Setup (one line)

Point the script at your own Infisical server. Either:

- export `INFISICAL_DOMAIN` (required on a fresh machine): the base URL of your Infisical instance, e.g. `export INFISICAL_DOMAIN=https://infisical.example.com` (Infisical Cloud users: `https://app.infisical.com`), or
- bake your default into the script by editing the `INFISICAL_DOMAIN="${INFISICAL_DOMAIN:-https://<your-infisical-host>}"` line near the top.

Optional: export `INFISICAL_TOKEN` (a machine identity token) to skip interactive login entirely (CI, agents, hooks).

## Run it

```
bash <skill-dir>/scripts/sync-env.sh <command> [environment]
```

(`<skill-dir>` is wherever you installed this skill, e.g. `~/.claude/skills/sync-env`.)

- `pull` (default): write Infisical secrets into local `.env` files. Existing files are backed up to `.env.bak` first.
- `push`: upload local `.env` files to Infisical (folders auto-created).
- `status`: diff local vs Infisical, write nothing.
- `bootstrap`: install CLI + log in + link repo (runs automatically before every command).
- `[environment]`: Infisical env slug, default `dev` (e.g. `dev`, `staging`, `prod`).

Examples:
```
bash <skill-dir>/scripts/sync-env.sh pull          # hydrate this machine (dev)
bash <skill-dir>/scripts/sync-env.sh push          # mirror local changes up (dev)
bash <skill-dir>/scripts/sync-env.sh status        # see drift
bash <skill-dir>/scripts/sync-env.sh pull staging  # hydrate staging
```

## What the script guarantees (preflight, every run)

1. **CLI present**: installs `infisical` if missing (macOS `brew`, Debian/RHEL install script; Arch points to AUR).
2. **Logged in**: checks `~/.infisical/infisical-config.json` for your Infisical host; if not, runs `infisical login --domain=$INFISICAL_DOMAIN` (OAuth). An exported `INFISICAL_TOKEN` (machine identity) skips the login. With no terminal attached (agents, CI, hooks) and no login or token, the script exits non-zero right away with the exact command a human must run, instead of hanging on a prompt. Agents should report that as a blocker.
3. **Repo linked**: must be a git repo with an `origin` remote. Project name = repo basename. If `.infisical.json` is missing, the script links **automatically and headlessly**: it reads the CLI's stored login token, resolves the Infisical project by name (creating it if absent) via the REST API, and writes `.infisical.json`. No interactive picker. (On platforms where the token cannot be read, e.g. some Linux keyring setups, it falls back to interactive `infisical init`.) Commit `.infisical.json` so the link travels to other machines.

## Conventions

- **Project = GitHub repo name**, bound by the committed `.infisical.json` (holds the workspace id). This is how another machine "knows" which secrets belong to a checkout.
- **`apps/<name>/.env` ↔ Infisical folder `/<name>`.** A single-app repo (root `.env`, no `apps/`) maps to root `/`.
- On `pull`, the script also pulls any Infisical folder that has no local app dir yet (creates `apps/<name>/`), so a fresh clone gets fully hydrated.

## Typical multi-machine flow

- **Machine A:** run any `sync-env` command once → the repo auto-links (project created if needed) and writes `.infisical.json`. Edit `apps/api/.env` (add `DATABASE_URL`, `REDIS_URL`) → `push` → secrets land in folder `/api` (env `dev`). Commit code + `.infisical.json` (never the `.env`).
- **Machine B:** `git pull` → run `pull` → `apps/api/.env` is recreated from Infisical → app runs.

## File-less alternative

To inject secrets straight into a process without writing a `.env`:
```
infisical run --path /api --env dev -- bun dev
```

## Notes

- Never commit `.env` files; keep them gitignored. Commit `.infisical.json`.
- `push` never deletes remote secrets implicitly; `pull` backs up before overwrite.
- For `staging`/`prod`, confirm with the user before pushing (higher stakes).
