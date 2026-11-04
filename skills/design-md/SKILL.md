---
name: design-md
description: "Generate UI that matches a specific brand's design language using a bundled DESIGN.md spec (colors, typography, spacing, components). Triggers: 'make it look like <brand>', 'build a <brand>-style page', 'use the Stripe design', 'match Linear's aesthetic', 'design-md', 'apply a DESIGN.md'. Brands include Apple, Stripe, Linear, Vercel, Notion, Airbnb, Spotify, Tesla, and ~63 more."
---

# Skill: design-md

A bundled library of brand design systems (`DESIGN.md` files) from voltagent/awesome-design-md. Each `library/<brand>/DESIGN.md` is a structured spec: color tokens, typography scales, spacing, radii, shadows, and component rules. Use it as the authoritative design language when building or restyling UI to match a brand.

## How To Use

1. Identify the brand the user wants (e.g. "make it look like Stripe" -> `stripe`). Match against the brand list below. If the user names a brand not in the library, say so and offer the closest available options.
2. Read `library/<brand>/DESIGN.md` (relative to this skill's directory) in full. The YAML frontmatter holds the tokens (`colors`, `typography`, spacing, etc.); the markdown body holds usage rules and patterns.
3. Treat that spec as the source of truth: apply its exact color values, font families/weights/sizes, letter-spacing, radii, and component conventions. Do not invent tokens that contradict it.
4. For the actual build/quality of the UI, pair this with the `frontend-design` skill — `design-md` supplies the *what* (the brand's tokens and rules), `frontend-design` supplies the *how* (production-grade, non-generic implementation).
5. If the user only wants the raw spec, copy `library/<brand>/DESIGN.md` into their project (commonly as `DESIGN.md` at the repo root) so their own agent can read it.

## Disambiguation

- If the user gives a vague vibe ("clean fintech look") rather than a brand, suggest 2-3 matching brands from the list and let them pick before building.
- Some brands have variants: `bmw` vs `bmw-m`. Confirm which if ambiguous.

## Available Brands

`airbnb` `airtable` `apple` `binance` `bmw` `bmw-m` `bugatti` `cal` `claude` `clay` `clickhouse` `cohere` `coinbase` `composio` `cursor` `elevenlabs` `expo` `ferrari` `figma` `framer` `hashicorp` `ibm` `intercom` `kraken` `lamborghini` `linear.app` `lovable` `mastercard` `meta` `minimax` `mintlify` `miro` `mistral.ai` `mongodb` `nike` `notion` `nvidia` `ollama` `opencode.ai` `pinterest` `playstation` `posthog` `raycast` `renault` `replicate` `resend` `revolut` `runwayml` `sanity` `sentry` `shopify` `slack` `spacex` `spotify` `starbucks` `stripe` `supabase` `superhuman` `tesla` `theverge` `together.ai` `uber` `vercel` `vodafone` `voltagent` `warp` `webflow` `wired` `wise` `x.ai` `zapier`

## Source & Updates

Vendored from https://github.com/voltagent/awesome-design-md (`design-md/<brand>/DESIGN.md`). To refresh, re-pull that repo and re-copy the `DESIGN.md` files into `library/`.
