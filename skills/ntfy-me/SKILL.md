---
name: ntfy-me
description: Send yourself or your team a push notification through any ntfy server (self-hosted or ntfy.sh), titled with the session it came from, with a kind (done, info, blocked, error, urgent), markdown body, a tap-to-open click URL, link buttons and file attachments. Use whenever you are told "ntfy me", "notify me", "ping me when done", "let me know on my phone", "send me a notification", "push me", or asked to tell someone when something finishes, even if ntfy is not named.
---

# ntfy me

Push a short notification to a phone and desktop through an ntfy server. Use it to **tell** someone something; use a call or chat message when you need an **answer**.

## When to send

- **You were asked:** "ntfy me", "notify me when the deploy is done", "let me know when you finish".
- **A long task someone is waiting on** reaches its result, or gets blocked on something only they can unblock.
- **Never** for routine progress, never for every step, and at most one per milestone. If nothing changed, don't send.

## Send

```bash
python3 scripts/ntfy_me.py "Deployed **voyager** to production. All checks green." --kind done \
  --action "Open site=https://example.com" --action "Pipeline=https://github.com/example/voyager/actions/runs/123"
```

The full form is `uv run --no-project python -I scripts/ntfy_me.py ...` (any Python 3.10+ works; there are no third-party dependencies).

| Option | What it does |
|---|---|
| `"message"` | The body, in markdown. If you leave it out, the body is read from stdin. `--plain` turns markdown off. |
| `--kind` | `done` ✅ (priority 3), `info` 💬 (2, the default), `blocked` ⚠️ (4), `error` ❌ (4), `urgent` 🚨 (5, breaks through Do Not Disturb, use only when someone asked to be woken up). |
| `--action "Label=https://..."` | A link button. Up to 3. |
| `--attach FILE` | Attaches a local file of 10 MB or less, such as a screenshot or PDF. ntfy keeps it for 24 hours. |
| `--attach-url URL` | Attaches a file that is already online. |
| `--title TEXT` | Overrides the automatic title. Rarely needed. |
| `--click URL` | What tapping the notification opens. Defaults to `NTFY_CLICK_URL` when set. |
| `--tags a,b` | Extra ntfy tags or emoji short names (`tada`, `rocket`). |
| `--priority 1-5` | Overrides the priority the kind would set. |
| `--dry-run` | Prints the resolved title and payload without sending. |

**Title:** it's resolved automatically, so don't pass one.
- If `NTFY_TITLE` is set, it's used as-is.
- In a session-based agent environment it's `<project> · <session title>` when the environment exposes one.
- Otherwise it's the current folder name, or `NTFY_TITLE_FALLBACK`.

## Writing the message

- **The first line is the outcome:** "Deployed voyager", "Tests failing on fuse-ios", "PR #61 merged".
- **Keep it to 5 short lines or fewer.** Details belong behind an action button, not in the notification.
- **Never include secrets,** tokens, passwords or customer data. It's a push notification shown on a lock screen.
- **Pick the kind honestly.** Use `error` or `blocked` for problems, and don't dress them up as `done`.
- **No em dashes.**

## After sending

- The command prints `{"sent": true, "id": ..., "title": ...}`. Mention in chat that you sent it and what it said.
- **On a non-zero exit,** stderr has ntfy's error, so report it.
  - 401 or 403: the token in `NTFY_TOKEN` is wrong or was revoked.
  - 413: the attachment is too big.

## Configuration

The script reads settings from `~/.config/ntfy-me/env` (mode 600), one `KEY=value` per line. Every value can be overridden by an environment variable of the same name.

| Variable | What it's for | Example value |
|---|---|---|
| `NTFY_HOST` | Base URL of the ntfy server, no trailing slash. | `https://ntfy.sh` or `https://ntfy.example.com` |
| `NTFY_TOPIC` | The topic to publish to. Subscribers follow this topic. | `my-alerts` |
| `NTFY_TOKEN` | Auth token for a user allowed to write to the topic. Leave empty only for a fully public server. | `tk_Ag1x2y3z...` |
| `NTFY_CLICK_URL` | Optional default URL opened when the notification is tapped. A `--click` flag wins over it. | `https://app.example.com/sessions/abc123` |
| `NTFY_TITLE` | Optional fixed title, skipping automatic resolution. | `CI bot` |
| `NTFY_TITLE_FALLBACK` | Title used when nothing else resolves. Defaults to the current folder name. | `build-server` |

Example `~/.config/ntfy-me/env`:

```env
NTFY_HOST=https://ntfy.sh
NTFY_TOPIC=my-alerts
NTFY_TOKEN=tk_Ag1x2y3zReplaceMe
```

- **Token scope:** create the token for an ntfy user that can only write to your topic; it can't read it or post anywhere else.
- **Receiving:** the ntfy app (phone or desktop) must be subscribed to your topic on your server.
- **Rotating the token:** on a self-hosted server, log in at `https://<your-host>/v1/account/token` and replace `NTFY_TOKEN`.
