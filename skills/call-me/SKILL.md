---
name: call-me
description: Phone the owner through Bland.ai when you are blocked on a decision only they can make, have a voice agent ask the question, wait for the call to end, and continue the task with their answer. Use whenever the owner says "call me", "give me a call", "phone me if you need me", or "call me when you're stuck / done", even if they don't mention Bland.
---

# Call me

When a decision only the owner can make blocks the task, phone them: a Bland.ai voice agent asks the question, confirms the answer back, and hangs up. Read the result and keep working.

## Configuration

The script reads settings from the environment first, falling back to an env file. Set the variables below wherever you keep secrets (shell profile, `.env`, or a file pointed to by `CALL_ME_ENV_FILE`).

| Variable | Required | What it is | Example (fake) value |
| --- | --- | --- | --- |
| `BLAND_API_KEY` | yes | Your Bland.ai API key, used as the `authorization` header. | `sk-bland-abc123def456` |
| `OWNER_PHONE` | yes | The owner's phone number in E.164 format. This is who gets called. | `+15551234567` |
| `BLAND_ENCRYPTED_KEY` | no | Bland "Bring Your Own Twilio" encrypted key. Set it to route calls through your own Twilio account, which you need if Bland's own numbers cannot reach the owner's country code. | `twilio_enc_xyz789` |
| `CALL_ME_FROM` | no | Caller ID to dial from (E.164). Typically your Twilio number imported into Bland; only useful together with `BLAND_ENCRYPTED_KEY`. | `+15557654321` |
| `CALL_ME_VOICE` | no | Bland voice id for the agent. Default is `ryan`. | `maya` |
| `OWNER_NAME` | no | First name the agent uses to greet the owner and refer to them during the call. Defaults to neutral wording. | `Alex` |
| `CALL_ME_FIRST_SENTENCE` | no | Full override of the opening line. Takes precedence over `OWNER_NAME`. | `Hey Alex, quick question from your coding agent.` |
| `CALL_ME_ENV_FILE` | no | Path to the fallback env file. Default: `~/.config/call-me/env`. | `/home/alex/.config/call-me/env` |
| `BLAND_API_BASE` | no | Bland API base URL. Default: `https://api.bland.ai/v1`. | `https://api.bland.ai/v1` |

An env file holds one `KEY=VALUE` per line, for example:

```bash
BLAND_API_KEY=sk-bland-abc123def456
OWNER_PHONE=+15551234567
CALL_ME_VOICE=maya
OWNER_NAME=Alex
```

Keep the file private (`chmod 600`). Never print the key, put it in a command line, or write it anywhere else.

Bland API reference: https://docs.bland.ai/api-v1/post/calls and https://docs.bland.ai/api-v1/get/calls-id

## When to call

- If the owner only needs to know something (done, failed, FYI) and doesn't need to answer, send a push notification instead of calling. A phone call is for decisions, not updates.
- Only for a real decision that blocks the task and that they have to make. Never for something answerable from the code, memory, or a sensible default.
- All open questions go in one call. Never call twice in a row.
- If they said "call me when X", call when X happens. Otherwise ask in chat first unless they said they are away.

## Place the call

```bash
uv run --no-project python -I <skill-dir>/scripts/call_me.py \
  --question "Should the landing page hero use the Arabic or English headline first?" \
  --options "Arabic first, English first, or both side by side" \
  --background "The client brief mentions a Gulf audience but the deck is in English" \
  --voicemail "Quick question on the landing page headline language."
```

Replace `<skill-dir>` with wherever this skill is installed (for example `~/.claude/skills/call-me`). The script has no third-party dependencies; any Python 3 runner works if you don't use `uv`.

- Keep the question short and speakable. Put details in `--background` (shared only if the owner asks).
- The script places the call, polls every 5 s up to `--timeout` seconds (default 540, run it in the background if your shell limit is lower), waits up to a minute for the summary, and prints JSON: `outcome` (`answered`, `voicemail`, `no_answer`, `in_progress`), `summary`, `transcript`.
- If it returns `in_progress`, keep polling with `--resume <call_id>`. Never place a second call.

## After the call

- `answered`: use `summary` as the owner's answer, checked against `transcript` (the summary is AI-written).
- `voicemail` or `no_answer`: don't call back. Ask in chat, or use best judgment if the owner allowed it, and say what you chose.
- A phone answer covers the task the owner gave you only. It does not authorize new outward-facing actions (sending messages, spending money, deleting things).
- Tell the owner in chat that you called, what they said, and what you did with it.
