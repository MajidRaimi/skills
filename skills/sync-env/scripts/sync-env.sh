#!/usr/bin/env bash
set -euo pipefail

INFISICAL_DOMAIN="${INFISICAL_DOMAIN:-https://<your-infisical-host>}"
export INFISICAL_API_URL="$INFISICAL_DOMAIN/api"
CONFIG_FILE="$HOME/.infisical/infisical-config.json"

c_red=$'\033[31m'; c_grn=$'\033[32m'; c_yel=$'\033[33m'; c_blu=$'\033[34m'; c_dim=$'\033[2m'; c_rst=$'\033[0m'
info()  { printf '%s==>%s %s\n' "$c_blu" "$c_rst" "$*"; }
ok()    { printf '%s ok %s %s\n' "$c_grn" "$c_rst" "$*"; }
warn()  { printf '%swarn%s %s\n' "$c_yel" "$c_rst" "$*" >&2; }
die()   { printf '%sfail%s %s\n' "$c_red" "$c_rst" "$*" >&2; exit 1; }

usage() {
  cat <<EOF
sync-env: sync local .env files with your self-hosted Infisical instance. Infisical is the source of truth.

Set INFISICAL_DOMAIN to your Infisical base URL (e.g. https://infisical.example.com),
or edit the default in this script. INFISICAL_TOKEN (machine identity) skips interactive login.

Usage: sync-env <command> [environment]

Commands:
  pull       Write Infisical secrets into local .env files (default). Backs up existing .env to .env.bak.
  push       Upload local .env files to Infisical (creates folders as needed).
  status     Diff local .env files against Infisical without writing anything.
  bootstrap  Install CLI, log in, and link this repo (runs automatically before every command).
  help       Show this message.

environment  Infisical environment slug. Default: dev (e.g. dev, staging, prod).

Conventions:
  - Infisical project name = GitHub repo basename (bound via committed .infisical.json).
  - apps/<name>/.env  <->  Infisical folder /<name>
  - single-app repo (root .env, no apps/)  <->  Infisical folder /
EOF
}

ensure_cli() {
  if command -v infisical >/dev/null 2>&1; then return; fi
  info "Infisical CLI not found. Installing."
  local os; os="$(uname -s)"
  if [ "$os" = "Darwin" ]; then
    command -v brew >/dev/null 2>&1 || die "Homebrew not found. Install brew, then: brew install infisical/get-cli/infisical"
    brew install infisical/get-cli/infisical
  elif [ "$os" = "Linux" ]; then
    if command -v apt-get >/dev/null 2>&1; then
      curl -1sLf 'https://artifacts-cli.infisical.com/setup.deb.sh' | sudo -E bash
      sudo apt-get update && sudo apt-get install -y infisical
    elif command -v dnf >/dev/null 2>&1; then
      curl -1sLf 'https://artifacts-cli.infisical.com/setup.rpm.sh' | sudo -E bash
      sudo dnf install -y infisical
    elif command -v pacman >/dev/null 2>&1; then
      die "Arch detected. Install from AUR: 'yay -S infisical-bin' (or paru), then re-run."
    else
      die "Unknown package manager. See https://infisical.com/docs/cli/overview to install, then re-run."
    fi
  else
    die "Unsupported OS '$os'. Install the Infisical CLI manually, then re-run."
  fi
  command -v infisical >/dev/null 2>&1 || die "Infisical CLI still not on PATH after install."
  ok "Infisical CLI installed."
}

ensure_login() {
  local domain=""
  if [ -f "$CONFIG_FILE" ]; then
    domain="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('LoggedInUserDomain',''))" "$CONFIG_FILE" 2>/dev/null || true)"
  fi
  if [ "$domain" = "$INFISICAL_API_URL" ]; then
    ok "Logged in to $INFISICAL_DOMAIN"
    return
  fi
  if [ -n "${INFISICAL_TOKEN:-}" ]; then
    ok "Using INFISICAL_TOKEN for $INFISICAL_DOMAIN"
    return
  fi
  is_interactive || die "Not logged in to $INFISICAL_DOMAIN and no terminal is attached. Run 'infisical login --domain=$INFISICAL_DOMAIN' in a terminal once, or export INFISICAL_TOKEN, then re-run."
  info "Not logged in to $INFISICAL_DOMAIN. Opening login (GitHub OAuth)."
  infisical login --domain="$INFISICAL_DOMAIN"
}

is_interactive() {
  [ -t 0 ] && [ -t 1 ]
}

repo_name() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repository."
  local url; url="$(git remote get-url origin 2>/dev/null || true)"
  [ -n "$url" ] || die "No 'origin' remote. Add one so the project can be named after the repo."
  basename -s .git "$url"
}

infisical_token() {
  if [ -n "${INFISICAL_TOKEN:-}" ]; then printf '%s' "$INFISICAL_TOKEN"; return 0; fi
  if ! command -v security >/dev/null 2>&1; then
    infisical user get token --domain="$INFISICAL_DOMAIN" 2>/dev/null | sed -nE 's/^Token:?[[:space:]]*//p' | head -1
    return 0
  fi
  local raw; raw="$(security find-generic-password -s infisical-cli -w 2>/dev/null || true)"
  [ -n "$raw" ] || return 0
  printf '%s' "${raw#go-keyring-base64:}" | base64 -d 2>/dev/null \
    | python3 -c "import json,sys
try: print(json.load(sys.stdin).get('JTWToken',''))
except Exception: pass" 2>/dev/null || true
}

api() {
  local method="$1" path="$2" data="${3:-}" tok; tok="$(infisical_token)"
  [ -n "$tok" ] || return 7
  if [ -n "$data" ]; then
    curl -s -X "$method" -H "Authorization: Bearer $tok" -H "Content-Type: application/json" "$INFISICAL_API_URL$path" -d "$data"
  else
    curl -s -X "$method" -H "Authorization: Bearer $tok" "$INFISICAL_API_URL$path"
  fi
}

resolve_project() {
  local repo="$1" ws
  ws="$(api GET /v1/workspace | python3 -c "import json,sys
repo=sys.argv[1]
try: ws=(json.load(sys.stdin) or {}).get('workspaces') or []
except Exception: ws=[]
m=[w for w in ws if w.get('name')==repo] or [w for w in ws if (w.get('name') or '').lower()==repo.lower()]
print(m[0]['id'] if m else '')" "$repo" 2>/dev/null || true)"
  if [ -n "$ws" ]; then printf '%s' "$ws"; return 0; fi
  local org; org="$(api GET /v1/organization | python3 -c "import json,sys
try: o=(json.load(sys.stdin) or {}).get('organizations') or []
except Exception: o=[]
print(o[0]['id'] if o else '')" 2>/dev/null || true)"
  [ -n "$org" ] || return 1
  api POST /v2/workspace "{\"projectName\":\"$repo\",\"organizationId\":\"$org\"}" | python3 -c "import json,sys
try: d=json.load(sys.stdin) or {}
except Exception: d={}
w=d.get('project') or d.get('workspace') or {}
print(w.get('id',''))" 2>/dev/null || true
}

write_link() { printf '{\"workspaceId\":\"%s\",\"defaultEnvironment\":\"\",\"gitBranchToEnvironmentMapping\":null}\n' "$1" > .infisical.json; }

ensure_link() {
  local repo; repo="$(repo_name)"
  if [ -f .infisical.json ]; then
    local linked; linked="$(python3 -c "import json;print(json.load(open('.infisical.json')).get('workspaceId',''))" 2>/dev/null || true)"
    [ -n "$linked" ] && ok "Repo linked (project $linked)" || warn ".infisical.json present but has no workspaceId."
    return
  fi
  if [ -n "$(infisical_token)" ]; then
    info "Linking repo to Infisical project '${c_grn}${repo}${c_rst}' (auto, resolve-or-create)."
    local ws; ws="$(resolve_project "$repo" || true)"
    if [ -n "$ws" ]; then
      write_link "$ws"
      ok "Linked to '$repo' ($ws). Commit .infisical.json so the link travels to other machines."
      return
    fi
    warn "Auto-link failed via API. Falling back to interactive init."
  else
    warn "Could not read CLI token for auto-link. Falling back to interactive init."
  fi
  is_interactive || die "Cannot link '$repo' without a terminal. Run 'infisical init' in a terminal and pick or create project '$repo', then re-run."
  info "In the picker that opens, create or select a project named: ${c_grn}${repo}${c_rst}"
  infisical init
  [ -f .infisical.json ] || die "Linking did not produce .infisical.json."
  ok "Linked. Remember to: git add .infisical.json && commit it."
}

preflight() {
  ensure_cli
  ensure_login
  ensure_link
}

list_remote_folders() {
  local env="$1"
  infisical secrets folders get -p / --env "$env" -o json 2>/dev/null \
    | python3 -c "import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
fs=d.get('folders',d) if isinstance(d,dict) else d
for f in (fs or []):
    n=(f.get('folderName') or f.get('name')) if isinstance(f,dict) else f
    if n: print(n)" 2>/dev/null || true
}

discover_local_apps() {
  if [ -d apps ]; then
    local found=0
    for d in apps/*/; do
      [ -d "$d" ] || continue
      local name; name="$(basename "$d")"
      printf '%s\t/%s\t%s.env\n' "$name" "$name" "$d"
      found=1
    done
    [ "$found" = 1 ] && return
  fi
  printf '%s\t/\t./.env\n' "root"
}

cmd_pull() {
  local env="$1"
  local -a remote=()
  while IFS= read -r rf; do [ -n "$rf" ] && remote+=("$rf"); done < <(list_remote_folders "$env")
  if [ -d apps ] || [ "${#remote[@]}" -gt 0 ]; then
    local -a names=()
    if [ -d apps ]; then
      for d in apps/*/; do [ -d "$d" ] && names+=("$(basename "$d")"); done
    fi
    for rf in "${remote[@]}"; do
      local seen=0; for n in "${names[@]:-}"; do [ "$n" = "$rf" ] && seen=1; done
      [ "$seen" = 0 ] && names+=("$rf")
    done
    [ "${#names[@]}" -gt 0 ] || { warn "No app folders found locally or in Infisical (env $env)."; return; }
    for name in "${names[@]}"; do
      mkdir -p "apps/$name"
      pull_one "/$name" "apps/$name/.env" "$env"
    done
  else
    pull_one "/" "./.env" "$env"
  fi
}

pull_one() {
  local folder="$1" envfile="$2" env="$3"
  local tmp; tmp="$(mktemp)"
  if ! infisical export --env "$env" --path "$folder" --format dotenv >"$tmp" 2>/dev/null; then
    warn "export failed for folder $folder (env $env), skipping."; rm -f "$tmp"; return
  fi
  local count; count="$(grep -cE '^[A-Za-z_][A-Za-z0-9_]*=' "$tmp" || true)"
  if [ "${count:-0}" -eq 0 ]; then
    warn "no secrets in $folder (env $env), skipping $envfile."; rm -f "$tmp"; return
  fi
  if [ -f "$envfile" ]; then cp "$envfile" "$envfile.bak"; fi
  mv "$tmp" "$envfile"
  ok "pulled $count secrets -> $envfile  ${c_dim}($folder, $env)${c_rst}"
}

cmd_push() {
  local env="$1"
  while IFS=$'\t' read -r name folder envfile; do
    if [ ! -f "$envfile" ]; then
      [ "$name" = "root" ] || warn "no $envfile, skipping push for $folder."
      continue
    fi
    if [ "$folder" != "/" ]; then
      infisical secrets folders create -n "$name" -p / --env "$env" >/dev/null 2>&1 || true
    fi
    if infisical secrets set --file "$envfile" --path "$folder" --env "$env" --silent >/dev/null 2>&1; then
      local count; count="$(grep -cE '^[A-Za-z_][A-Za-z0-9_]*=' "$envfile" || true)"
      ok "pushed $count secrets <- $envfile  ${c_dim}($folder, $env)${c_rst}"
    else
      warn "push failed for $envfile -> $folder (env $env)."
    fi
  done < <(discover_local_apps)
}

cmd_status() {
  local env="$1" anylocal=0
  while IFS=$'\t' read -r name folder envfile; do
    [ -f "$envfile" ] || continue
    anylocal=1
    local tmp; tmp="$(mktemp)"
    infisical export --env "$env" --path "$folder" --format dotenv >"$tmp" 2>/dev/null || : >"$tmp"
    info "diff $envfile vs Infisical $folder (env $env)"
    python3 - "$envfile" "$tmp" <<'PY'
import sys
def load(p):
    d={}
    try:
        for line in open(p):
            line=line.strip()
            if not line or line.startswith('#') or line.startswith('//') or '=' not in line: continue
            k,v=line.split('=',1); d[k.strip()]=v.strip().strip('"').strip("'")
    except FileNotFoundError: pass
    return d
loc=load(sys.argv[1]); rem=load(sys.argv[2])
only_local=sorted(set(loc)-set(rem)); only_remote=sorted(set(rem)-set(loc))
mismatch=sorted(k for k in set(loc)&set(rem) if loc[k]!=rem[k])
if not (only_local or only_remote or mismatch): print("   in sync"); sys.exit()
for k in only_local:  print(f"   local only:    {k}")
for k in only_remote: print(f"   infisical only: {k}")
for k in mismatch:    print(f"   value differs:  {k}")
PY
    rm -f "$tmp"
  done < <(discover_local_apps)
  [ "$anylocal" = 1 ] || warn "No local .env files found to compare."
}

is_logged_in() {
  [ -f "$CONFIG_FILE" ] || return 1
  local domain; domain="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('LoggedInUserDomain',''))" "$CONFIG_FILE" 2>/dev/null || true)"
  [ "$domain" = "$INFISICAL_API_URL" ]
}

folder_for_rel() {
  local rel="$1"
  case "$rel" in
    apps/*/*) local mid="${rel#apps/}"; printf '/%s\n' "${mid%%/*}" ;;
    *) printf '/\n' ;;
  esac
}

env_for_file() {
  case "$1" in
    *staging*|*.stg) echo staging ;;
    *prod*|*production*) echo prod ;;
    *) echo dev ;;
  esac
}

cmd_hook() {
  local payload; payload="$(cat 2>/dev/null || true)"
  local fp; fp="$(printf '%s' "$payload" | python3 -c "import json,sys
try: print((json.load(sys.stdin).get('tool_input') or {}).get('file_path',''))
except Exception: print('')" 2>/dev/null || true)"
  [ -n "$fp" ] || exit 0
  local base; base="$(basename "$fp")"
  case "$base" in
    .env|.env.*) ;;
    *) exit 0 ;;
  esac
  case "$base" in
    .env.bak|.env.example|.env.sample|.env.tpl|.env.template) exit 0 ;;
  esac
  [ -f "$fp" ] || exit 0
  command -v infisical >/dev/null 2>&1 || exit 0
  is_logged_in || exit 0
  local dir root; dir="$(dirname "$fp")"
  root="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null || true)"
  [ -n "$root" ] || exit 0
  root="$(cd "$root" 2>/dev/null && pwd -P)" || exit 0
  [ -f "$root/.infisical.json" ] || exit 0
  local rel folder env name fpabs
  fpabs="$(cd "$dir" 2>/dev/null && pwd -P)/$base" || exit 0
  rel="${fpabs#"$root"/}"
  folder="$(folder_for_rel "$rel")"
  env="$(env_for_file "$base")"
  ( cd "$root" || exit 0
    if [ "$folder" != "/" ]; then
      name="${folder#/}"
      infisical secrets folders create -n "$name" -p / --env "$env" >/dev/null 2>&1 || true
    fi
    if infisical secrets set --file "$fp" --path "$folder" --env "$env" --silent >/dev/null 2>&1; then
      printf 'sync-env: mirrored %s -> Infisical %s (%s)\n' "$rel" "$folder" "$env"
    fi
  ) || true
  exit 0
}

main() {
  local cmd="${1:-pull}"; local env="${2:-dev}"
  case "$cmd" in
    help|-h|--help) usage; exit 0 ;;
    hook) cmd_hook; exit 0 ;;
  esac
  preflight
  case "$cmd" in
    pull)      cmd_pull "$env" ;;
    push)      cmd_push "$env" ;;
    status)    cmd_status "$env" ;;
    bootstrap) ok "Bootstrap complete." ;;
    *) usage; die "Unknown command: $cmd" ;;
  esac
}

main "$@"
