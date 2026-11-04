# Feature Scaffolding

Complete template for a feature folder. Uses `projects` as the example feature.

## Full Feature Structure

```
app/(dashboard)/projects/
├── params.ts
├── prefetch.ts
├── page.tsx
├── fallback.tsx
├── _hooks/
│   ├── use-projects-params.ts
│   └── use-projects.ts
├── _validations/
│   └── project-schemas.ts
├── _components/
│   ├── projects-view.tsx
│   ├── project-card.tsx
│   └── project-form.tsx
└── _sections/                # optional — for section-based pages
    ├── hero.tsx
    └── features.tsx
```

## File Contents

### `params.ts` — Search Param Definitions

```ts
import { createLoader, parseAsInteger, parseAsString } from "nuqs/server";
import { PAGINATION } from "@/core/constants";

export const projectsParams = {
  search: parseAsString.withDefault("").withOptions({ clearOnDefault: true }),
  page: parseAsInteger
    .withDefault(PAGINATION.DEFAULT_PAGE)
    .withOptions({ clearOnDefault: true }),
  pageSize: parseAsInteger
    .withDefault(PAGINATION.DEFAULT_PAGE_SIZE)
    .withOptions({ clearOnDefault: true }),
};

export const loadProjectsParams = createLoader(projectsParams);
```

### `_hooks/use-projects-params.ts` — Client-Side Params

```ts
"use client";

import { useQueryStates } from "nuqs";
import { projectsParams } from "../params";

export const useProjectsParams = () => useQueryStates(projectsParams);
```

### `_hooks/use-projects.ts` — Query + Mutation Hooks

Single file for all queries and mutations. See [Async State](async-state.md) for detailed patterns.

```ts
"use client";

import { useMutation, useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useProjectsParams } from "./use-projects-params";
import type { Project, CreateProjectInput } from "../_validations/project-schemas";

// Query options — exported for use in prefetch.ts
export const projectsQueryOptions = (params: Record<string, unknown>) => ({
  queryKey: ["projects", params],
  queryFn: () =>
    api.get<{ data: Project[]; total: number }>("/projects", { params }).then((res) => res.data),
});

// Query hook — uses useSuspenseQuery for SSR hydration
export const useProjects = () => {
  const [params] = useProjectsParams();
  return useSuspenseQuery(projectsQueryOptions(params));
};

// Mutation hook — invalidates queries + shows toast
export const useCreateProject = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateProjectInput) => api.post("/projects", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project created");
    },
    onError: () => toast.error("Failed to create project"),
  });
};

// Additional mutations follow the same pattern (update, delete)
```

### `_validations/project-schemas.ts`

```ts
import { z } from "zod";

export const projectSchema = z.object({
  id: z.string(),
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  status: z.enum(["active", "archived"]),
  createdAt: z.string().datetime(),
});

export const createProjectSchema = projectSchema.omit({ id: true, createdAt: true });

export type Project = z.infer<typeof projectSchema>;
export type CreateProjectInput = z.infer<typeof createProjectSchema>;
```

### `prefetch.ts`

```ts
import { dehydrate } from "@tanstack/react-query";
import { getQueryClient } from "@/lib/get-query-client";
import { projectsQueryOptions } from "./_hooks/use-projects";

export const prefetchProjects = async (params: Record<string, unknown>) => {
  const queryClient = getQueryClient();
  await queryClient.prefetchQuery(projectsQueryOptions(params));
  return dehydrate(queryClient);
};
```

### `fallback.tsx`

```tsx
import { Skeleton } from "@/components/ui/skeleton";

export const ProjectsFallback = () => (
  <div className="space-y-4">
    <Skeleton className="h-10 w-full" />
    <div className="grid gap-4 md:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Skeleton key={i} className="h-32 w-full rounded-lg" />
      ))}
    </div>
  </div>
);
```

### `page.tsx`

See [Page Patterns](page-patterns.md) for the full pattern. The page wires together: `loadProjectsParams` → `prefetchProjects` → `HydrationBoundary` → `Suspense` → `ProjectsView`.

### `_components/projects-view.tsx` — Client Container

See [Components & State](components-and-state.md). The view calls `useProjects()` and `useProjectsParams()`, passes data to presenters.

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Params file | `params.ts` | `params.ts` |
| Param hook | `use-[feature]-params.ts` | `use-projects-params.ts` |
| Query/mutation hook | `use-[feature].ts` (plural) | `use-projects.ts` |
| Validation | `[singular]-schemas.ts` | `project-schemas.ts` |
| Container component | `[feature]-view.tsx` (plural) | `projects-view.tsx` |
| Presenter component | `[singular]-[variant].tsx` | `project-card.tsx` |
| Form component | `[singular]-form.tsx` | `project-form.tsx` |
| Fallback | `fallback.tsx` | `fallback.tsx` |
| Section component | `[descriptive-name].tsx` | `hero.tsx`, `cta.tsx` |
