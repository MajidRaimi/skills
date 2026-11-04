#!/usr/bin/env bash
set -uo pipefail

repo="$1"
project="$2"
stale_minutes="${3:-45}"
state="$repo/.claude/ralph-loop.local.md"
ended="$repo/.claude/prd-loop.ended"
warned=0
notify_cmd="${PRD_LOOP_NOTIFY_CMD:-}"

notify() {
  [[ -n "$notify_cmd" ]] && command -v "${notify_cmd%% *}" >/dev/null 2>&1 && $notify_cmd "$1" --kind error --title "$project · prd-loop"
  return 0
}

modified_at() {
  stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0
}

while true; do
  sleep "${PRD_LOOP_WATCH_INTERVAL:-300}"
  if [[ ! -f "$state" ]]; then
    [[ -f "$ended" ]] || notify "$project: the loop stopped without finishing (hook error, /clear, or the session ended). Check the task file and git log."
    exit 0
  fi
  last_commit=$(git -C "$repo" log -1 --format=%ct 2>/dev/null || echo 0)
  last_round=$(modified_at "$state")
  newest=$(( last_commit > last_round ? last_commit : last_round ))
  if (( $(date +%s) - newest > stale_minutes * 60 )); then
    (( warned )) || notify "$project: the loop looks stuck, no commit or new round for ${stale_minutes} minutes (API error, usage limit or a hung command)."
    warned=1
  else
    warned=0
  fi
done
