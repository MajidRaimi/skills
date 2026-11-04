# Agent briefs

Fill in `<REPO>` (absolute path), `<PRODUCT>`, `<DATE>` and `<SOURCES>` (research notes, landing copy, schemas, hosting notes that exist in this repo). Cut topics that don't apply to this product and add ones `DECISIONS.md` raises.

## Shared rules (start every writer prompt with these)

```
You are writing product documentation for <PRODUCT>. Repo <REPO>, branch docs/product-spec is checked out: do not commit, push or switch branches. You own ONLY the files named below; do not edit anything else.

Read first: <REPO>/docs/product/DECISIONS.md (the source of truth from the product owner: follow it exactly and never contradict it; if you think it needs a change, say so in your report, never edit it), then ~/.claude/CLAUDE.md (the user's engineering rules) and any other engineering conventions file the workspace provides (feature-first layout, Turborepo with mprocs, Bun and uv, docker compose and .env.example, an env-var manager), then <SOURCES>.

Use the names in DECISIONS.md section 0 (Vocabulary) exactly: product name, domains, app and service names, roles, entities, status enums, plan names, channel names. Never rename or add synonyms; if you need a name that isn't there, mark it "Assumption:" and list it in your report.

Rules: plain, concrete English with no marketing fluff. No em dashes or en dashes anywhere (use commas, colons, parentheses). No invented facts or numbers: prices, quotas and targets are named placeholders like PLAN_TEAM_SEAT_MONTHLY or TBD. Mark everything not in DECISIONS.md as "Assumption:". Cite URLs for researched claims; mark unsupported claims about third-party services "Unverified:". Diagrams in mermaid. Be exhaustive: the product owner wants every aspect covered. Link to DECISIONS.md near the top and to sibling documents where relevant. Return a 5 line summary plus any new names you introduced and any DECISIONS.md changes you think are needed.
```

Writers that research need: `Research with WebSearch/WebFetch (load them via ToolSearch "select:WebSearch,WebFetch") and cite URLs.`

## PRD.md

```
Write <REPO>/docs/product/PRD.md. Use the to-spec skill template (read the to-spec skill's SKILL.md under the user's skills directory, for example ~/.claude/skills/to-spec/SKILL.md) for structure, but write to the file, not an issue tracker, and interview nobody.

Sections: Problem statement; Solution; Personas (every user type and staff role in DECISIONS.md); User stories (a long numbered list grouped by feature area, one area per feature in DECISIONS.md plus signup, members and roles, billing, notifications, audit trail, data retention, admin panel, security); Functional requirements per area with IDs (FR-<AREA>-N) and acceptance criteria; Non-functional requirements (performance targets, availability, data residency, compliance, accessibility WCAG 2.1 AA, RTL and bilingual support if relevant, browser support); Success metrics with TBD targets where unknown; Out of scope (v1 non-goals and v2 items); Risks and mitigations; Open questions; Glossary of domain terms.
```

## PRODUCT.md and DESIGN.md

```
Produce <REPO>/PRODUCT.md and <REPO>/DESIGN.md (repo root, where impeccable expects them), plus any sidecar impeccable's document step writes. Invoke the Skill tool with skill "impeccable", then follow its reference/init.md for PRODUCT.md and reference/document.md for DESIGN.md. Do NOT ask the user questions; answer every init question from DECISIONS.md and the existing code.

PRODUCT.md: what <PRODUCT> is, users and their jobs, positioning, voice and tone (per language if bilingual), principles, what the product never claims, surfaces (marketing site, workspace, admin), platform.

DESIGN.md: document the real current system from the code if there is one (theme rules, color tokens with hex values, typography, radius, icons, motion and reduced motion, imagery, RTL and bidi rules, existing components). Then a section "Workspace and admin UI" that extends it to the product app: app shell with pinned header and toolbar and internally scrolling content, tables, list and detail split views, upload states, empty, loading and error states, notifications, dense data typography. With no existing UI, propose a system and mark it "Assumption:".
```

## ARCHITECTURE.md, AI-ENGINE.md, SECURITY.md

```
Write <REPO>/docs/product/ARCHITECTURE.md, AI-ENGINE.md and SECURITY.md. Also read the current repo layout (package.json, turbo.json, mprocs.yaml, docker-compose.yml, apps/*) and any hosting skill notes DECISIONS.md points to. Research every named technology and cite URLs.

ARCHITECTURE.md: system context and container diagrams; the Turborepo layout (apps/* and packages/*, feature-first inside each app); service responsibilities and boundaries; the main request flows end to end; data stores and their layout; auth design; multi-tenancy isolation; i18n architecture; frontend data layer (TanStack Query with hydration and axios, generated API client, Zustand, nuqs, react-hook-form with zod); observability; deployment per service with domains; local dev (docker compose services, mprocs order, .env.example defaults); CI and release; backups and disaster recovery; scaling path; an ADR list of key decisions with rejected alternatives.

AI-ENGINE.md: the pipeline end to end (ingestion, parsing, chunking, embeddings, retrieval); the agent design (runtime, sandbox, tools, sub-agents, a verifier pass); deterministic calculations in code, never by the model; model gateway and per-task routing decided by evals; job orchestration (queues, retries, idempotency, cancellation, timeouts, progress events); usage metering and cost per tenant; the eval suite with benchmarks, metrics and a release gate; failure modes and safeguards (prompt injection from inputs, hallucinated references); data handling (where data lives, no training on customer data).

SECURITY.md: threat model; tenant isolation; authn and authz matrix by role; secrets management (the env-var manager the user's setup uses); encryption in transit and at rest; upload safety; append-only audit trail; support access with consent; retention and deletion; the compliance mappings DECISIONS.md names; incident response and breach notification; vulnerability management; rate limiting and abuse; logging without PII.
```

## DATA-MODEL.md, API.md

```
Write <REPO>/docs/product/DATA-MODEL.md and API.md. Also read any existing schemas and migrations in the repo and the data shapes in the existing code.

DATA-MODEL.md: database and ORM from DECISIONS.md; id strategy, timestamps, tenant column with row level security on every tenant table, soft delete where needed; an ER diagram; every table with columns, types, constraints, indexes and notes, covering tenants, users, roles, auth, every feature in DECISIONS.md, billing, notifications, audit events, admin staff, evals; enumerations; the RLS policy pattern; retention and deletion cascades; which tables are append only.

API.md: base URL and versioning, the contract format (OpenAPI with a generated TypeScript client); conventions (auth, CSRF, idempotency keys, cursor pagination, error envelope with stable codes and localized messages, rate limits, Accept-Language); then every endpoint grouped by area with method, path, purpose, role required, and request and response shapes for the important ones, including the admin API; the real-time channel and event catalogue with payload schemas if there is real-time; webhooks received.
```

## BILLING.md, ROADMAP.md

```
Write <REPO>/docs/product/BILLING.md and ROADMAP.md. Research the payment and invoicing providers DECISIONS.md names (subscriptions, tokenization, local payment methods, webhooks and signatures, refunds, proration, test mode) and the tax and e-invoicing rules that apply; read any matching skill notes the workspace provides for a named invoicing provider.

BILLING.md: plans with placeholder prices and quotas; what differs between plans; trial and what happens at expiry; seats (paid and free roles); seat changes and proration; monthly vs annual; usage quota mechanics (what counts, when debited, ledger, reset, top-ups, behavior at zero, alerts at 80 and 100 percent); payment flow, retries, dunning, past_due and suspension, grace period; invoicing and tax; refunds and cancellations; enterprise contracts; admin billing operations; webhooks and idempotency; subscription state machine in mermaid; edge cases; metrics to track. Mark provider unknowns clearly.

ROADMAP.md: phases from today's repo state to the first milestone in DECISIONS.md. Phase 0 is foundations (monorepo apps, docker compose services, auth, CI, deployment). Each phase has goal, scope, deliverables, exit criteria and dependencies, sized S, M or L, never calendar dates. Every v1 feature in DECISIONS.md section 4 lands in some phase (PRD.md is being written at the same time, so don't wait for it; the review checks the PRD against the roadmap afterwards). Size each phase so it can be built by one autopilot loop (about 40 small tasks or fewer); split bigger ones. Exit criteria must be checkable by running something (a test, a command, a URL, a browser flow), never "works well". Then v2 candidates, a risk list and the critical path.
```

## Cross-document review

```
You are a skeptical reviewer of <PRODUCT>'s product documentation. Repo <REPO>, branch docs/product-spec (do not commit, push or switch). Source of truth: docs/product/DECISIONS.md, which you never edit (list needed changes in your report). Review and fix: <the files written>.

Hunt for real problems, not style:
1. Contradictions with DECISIONS.md: check every Decided row against every document.
2. Contradictions between documents: role names and permission sets (PRD vs SECURITY vs API vs DATA-MODEL); entity, enum and status names across DATA-MODEL, API and PRD; endpoint paths mentioned anywhere that don't exist in API.md; channel and event names; domains and subdomains; trial, quota and dunning behavior; plan feature differences; every v1 PRD feature appearing in a ROADMAP phase.
3. Factual risks: third-party claims stated as fact without a source get marked "Unverified:".
4. House rules: no em or en dashes (grep for them), no invented numbers presented as real, no certification claims, names match DECISIONS.md section 0 (Vocabulary).

Fix every issue directly with minimal, precise edits. Then write docs/product/REVIEW-NOTES.md with: 1. how conflicts were resolved; 2. what you fixed (file and section), plus a coverage table with one row per Decided item in DECISIONS.md and the document sections where it lands (flag any that land nowhere); 3. decisions for the product owner, numbered D1, D2, ... each with your recommended answer; 4. top open questions consolidated from all documents (deduplicated, at most 20, each with the default assumed). Return a summary under 250 words.
```

## Propagate decisions

```
Repo <REPO>, branch docs/product-spec (do not commit, push or switch). Read docs/product/DECISIONS.md, especially section "7. Review follow-ups", and docs/product/REVIEW-NOTES.md section 3. Apply every item of section 7 to all affected documents with precise edits, keeping each document internally consistent (permission matrices, endpoints, columns, acceptance criteria, roadmap items). Then mark the matching D items in REVIEW-NOTES.md section 3 as resolved with the chosen answer and leave the rest as proposals. No em or en dashes (grep to confirm). Return a short list of files changed.
```
