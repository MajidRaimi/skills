---
name: nextjs-patterns
description: >
  Guide for building Next.js applications following a specific architecture
  with App Router, Zustand, TanStack Query, Axios, nuqs, react-hook-form,
  and Zod. Use when scaffolding features, creating components, setting up
  state management, building forms, or working with search params in
  Next.js projects.
---

# Next.js App Router Architecture

## Architecture Overview

All code lives under `src/`. Four top-level directories sit next to `/app`:

| Directory | Purpose |
|-----------|---------|
| `core/` | Shared application logic — constants, hooks, providers, stores, types, utils |
| `lib/` | External integrations — API client (Axios), auth, db, email |
| `components/` | Global UI — `ui/` (shadcn/design system), `custom/` (reusable composites) |
| `app/` | Routes and feature folders (co-located) |

### Tech Stack

| Concern | Library |
|---------|---------|
| Local state | Zustand |
| Async state | TanStack Query + Axios |
| Forms | react-hook-form + Zod |
| Search params | nuqs |
| UI | shadcn / Radix |
| Translations | Tolgee |

## Feature Scaffolding Checklist

Every route-level feature lives inside its `app/` segment and follows this structure:

```
app/(dashboard)/projects/
├── params.ts                    # nuqs search param definitions
├── prefetch.ts                  # server-side QueryClient + prefetch
├── page.tsx                     # server component (entry point)
├── fallback.tsx                 # loading skeleton for Suspense
├── _hooks/
│   ├── use-projects-params.ts   # useQueryStates wrapper
│   └── use-projects.ts          # query + mutation hooks
├── _validations/
│   └── project-schemas.ts       # Zod schemas for forms
├── _components/
│   ├── projects-view.tsx         # main client container
│   ├── project-card.tsx          # presentational
│   └── project-form.tsx          # form with react-hook-form
└── _sections/                   # optional — for section-based pages
    ├── hero.tsx
    └── features.tsx
```

### Creation Workflow

1. Define search params in `params.ts`
2. Create Zod schemas in `_validations/`
3. Write query/mutation hooks in `_hooks/`
4. Build `_components/` — container first, then presenters
5. Create `prefetch.ts` for server-side data loading
6. Create `fallback.tsx` skeleton
7. Wire everything in `page.tsx` with Suspense + HydrationBoundary

## Core Patterns Quick Reference

**Query hook:**
```ts
export const projectsQueryOptions = (params: ProjectParams) => ({
  queryKey: ["projects", params],
  queryFn: () => api.get("/projects", { params }).then((res) => res.data),
});

export const useProjects = () => {
  const [params] = useProjectsParams();
  return useSuspenseQuery(projectsQueryOptions(params));
};
```

**Search params:**
```ts
export const projectsParams = {
  search: parseAsString.withDefault("").withOptions({ clearOnDefault: true }),
  page: parseAsInteger.withDefault(1).withOptions({ clearOnDefault: true }),
};

export const useProjectsParams = () => useQueryStates(projectsParams);
```

**Zustand store:**
```ts
export const useProjectStore = create<ProjectStore>()((set) => ({
  selectedId: null,
  setSelectedId: (id) => set({ selectedId: id }),
}));
```

**Page pattern:**
```tsx
export default async function ProjectsPage({ searchParams }: PageProps) {
  const params = await loadProjectsParams(searchParams);
  const dehydratedState = await prefetchProjects(params);
  return (
    <HydrationBoundary state={dehydratedState}>
      <Suspense fallback={<ProjectsFallback />}>
        <ProjectsView />
      </Suspense>
    </HydrationBoundary>
  );
}
```

## Key Rules

- **Underscore prefixes** — `_components/`, `_hooks/`, `_validations/`, `_sections/` prevent Next.js route resolution
- **`_sections/`** — Optional folder for large pages (landing, marketing); sections are server components by default
- **Co-location** — Feature code lives with its route; shared code goes in `core/`
- **Naming** — Feature-prefix all files: `project-card.tsx`, `use-projects.ts`
- **One hook file** — Put all query + mutation hooks for a feature in a single file
- **`useSuspenseQuery`** — Always use for SSR-hydrated queries (not `useQuery`)
- **Barrel exports** — Use `index.ts` in `core/` subdirectories (e.g., `core/constants/index.ts`)
- **No fetch** — Use the Axios api instance from `lib/` for all HTTP calls
- **Providers** — Compose into `root-provider.tsx`, import in root `layout.tsx`

## References

- [Folder Structure](references/folder-structure.md) — Full directory breakdown and placement rules
- [Feature Scaffolding](references/feature-scaffolding.md) — Complete feature template with file contents
- [Async State](references/async-state.md) — Axios setup, queries, mutations, hydration
- [Forms & Params](references/forms-and-params.md) — react-hook-form, Zod, nuqs patterns
- [Components & State](references/components-and-state.md) — Component structure, Zustand, providers
- [shadcn/ui](references/shadcn-ui.md) — Component installation, configuration, RTL support
- [Metadata & SEO](references/metadata-and-seo.md) — generateMetadata, OG images, title templates
- [Page Patterns](references/page-patterns.md) — Server components, prefetch, Suspense, layouts
- [Translations](references/translations.md) — Tolgee i18n, server/client translations, language switching
