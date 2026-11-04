# Forms & Params

react-hook-form + Zod for forms. nuqs for URL search params.

## Zod Schemas

Define schemas in `_validations/[singular]-schemas.ts`. Export both schemas and inferred types.

```ts
import { z } from "zod";

export const createProjectSchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string().optional(),
  status: z.enum(["active", "archived"]).default("active"),
});

export type CreateProjectInput = z.infer<typeof createProjectSchema>;
```

## react-hook-form Setup

Use `zodResolver` to connect Zod schemas with react-hook-form.

```tsx
"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { createProjectSchema, type CreateProjectInput } from "../_validations/project-schemas";
import { useCreateProject } from "../_hooks/use-projects";

export const ProjectForm = () => {
  const { mutate, isPending } = useCreateProject();

  const form = useForm<CreateProjectInput>({
    resolver: zodResolver(createProjectSchema),
    defaultValues: { name: "", description: "", status: "active" },
  });

  const onSubmit = form.handleSubmit((data) => {
    mutate(data, { onSuccess: () => form.reset() });
  });

  return (
    <form onSubmit={onSubmit}>
      {/* Use shadcn Form components or direct register */}
      <input {...form.register("name")} />
      {form.formState.errors.name && (
        <p>{form.formState.errors.name.message}</p>
      )}
      <button type="submit" disabled={isPending}>
        {isPending ? "Creating..." : "Create"}
      </button>
    </form>
  );
};
```

### Key Points

- `zodResolver` handles validation — no manual `validate` functions
- `form.handleSubmit` wraps submission — only fires `mutate` if valid
- Connect to mutation hooks for API calls
- Use `isPending` from mutation to disable submit button

## nuqs Search Params

### Defining Params

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

### Server-Side Parsing

Use `createLoader` + `loadParams` in server components:

```tsx
export default async function Page({ searchParams }: PageProps) {
  const params = await loadProjectsParams(searchParams);
  // params is fully typed: { search: string; page: number; pageSize: number }
}
```

### Client-Side Usage

Use `useQueryStates` in a dedicated hook:

```ts
"use client";

import { useQueryStates } from "nuqs";
import { projectsParams } from "../params";

export const useProjectsParams = () => useQueryStates(projectsParams);
```

Usage in components:

```tsx
const [params, setParams] = useProjectsParams();

// Read
params.search; // string
params.page;   // number

// Update (merges with existing params)
setParams({ search: "new query" });
setParams({ page: 2 });
setParams({ search: "", page: 1 }); // reset
```

### Connecting Params to Query Keys

Params flow into query keys so TanStack Query refetches when URL changes:

```ts
export const projectsQueryOptions = (params: Record<string, unknown>) => ({
  queryKey: ["projects", params],  // params in key = auto-refetch on change
  queryFn: () => api.get("/projects", { params }).then((res) => res.data),
});
```

### Options

- `clearOnDefault: true` — Removes param from URL when set to default value (keeps URLs clean)
- `withDefault(value)` — Sets a default so the param is never `null`

### Pagination Constant

```ts
// core/constants/pagination.ts
export const PAGINATION = {
  DEFAULT_PAGE: 1,
  DEFAULT_PAGE_SIZE: 10,
} as const;
```
