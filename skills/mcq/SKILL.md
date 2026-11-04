---
name: mcq
description: Ask the user questions as multiple-choice (MCQ) with the AskUserQuestion tool instead of plain text. Use whenever the user says "mcq", "/mcq", "mcq skill", "ask me as MCQ", "use the AskUserQuestion tool", or puts "mcq" in front of a request, e.g. "mcq what should we name the app" or "mcq the auth plan".
---

# MCQ

Whatever comes with this skill becomes multiple-choice questions asked through the **AskUserQuestion** tool. Never ask in plain chat text while this skill is active.

## How to turn the request into MCQs

1. **Read the request** that came with the skill (the arguments, or the message that mentioned mcq). If it's empty, use the open question or decision from the conversation so far.
2. **Do the homework first.** Look at the code, files, memory or conversation so the options are real and specific, not generic. Never ask something you can answer yourself.
3. **Find the decisions.** Split the request into the 1 to 4 most important choices the user needs to make. Each one becomes a question.
4. **Ask with AskUserQuestion:**
   - 2 to 4 concrete, mutually exclusive options per question. Don't add an "Other" option; the tool adds one.
   - Put your recommended option first and end its label with "(Recommended)".
   - Labels are 1 to 5 words. Descriptions say what happens and the trade-off in one sentence.
   - `header` is a chip of 12 characters or fewer.
   - Use `multiSelect: true` when choices can combine (features, platforms, which items to include).
   - Add `preview` when options are code, layouts, configs or text the user needs to compare side by side (single-select only).
5. **More than 4 decisions?** Ask the most important round first, then the next round, based on the user's answers.
6. **After the user answers,** state the choices back in one or two lines and carry on with the task using them. Don't ask again about anything they already answered.

## Examples

- "mcq what should I name the new app" → one question, 4 name options with the reasoning in each description.
- "mcq plan the login feature" → questions on auth method, providers (multiSelect), session storage, UI style with previews.
- "mcq which of these PRs should I merge" → one multiSelect question listing the PRs.
- "mcq" alone after you proposed something → turn the open choices in your last message into questions.

## Rules

- Write in the user's style.
- If the user rejects the question, stop and wait for them to explain.
