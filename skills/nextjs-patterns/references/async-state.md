# Async State

Axios for HTTP, TanStack Query for caching/fetching, server-side hydration for SSR.

## Axios API Instance

All HTTP calls go through a single Axios instance at `lib/api.ts`.

```ts
import axios from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Auth header interceptor
api.interceptors.request.use((config) => {
  const token = getAccessToken(); // from your auth solution
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // handle unauthorized (e.g., redirect to login)
    }
    return Promise.reject(error);
  }
);
```

## Query Options Pattern

Define query options as standalone functions — reusable in both hooks and prefetch.

```ts
export const projectsQueryOptions = (params: Record<string, unknown>) => ({
  queryKey: ["projects", params],
  queryFn: () =>
    api.get<ProjectsResponse>("/projects", { params }).then((res) => res.data),
});

export const projectQueryOptions = (id: string) => ({
  queryKey: ["projects", id],
  queryFn: () => api.get<Project>(`/projects/${id}`).then((res) => res.data),
});
```

### Query Key Conventions

| Scope | Key shape | Example |
|-------|-----------|---------|
| List (filtered) | `[feature, params]` | `["projects", { page: 1 }]` |
| Single item | `[feature, id]` | `["projects", "abc123"]` |
| Nested resource | `[parent, parentId, child, params]` | `["projects", "abc", "tasks", { status: "open" }]` |

## Query Hooks

Always use `useSuspenseQuery` for SSR-hydrated data — it integrates with React Suspense and guarantees data is defined.

```ts
export const useProjects = () => {
  const [params] = useProjectsParams();
  return useSuspenseQuery(projectsQueryOptions(params));
};
```

> `useSuspenseQuery` returns `{ data }` where `data` is never `undefined`. No loading states needed — Suspense handles it.

## Mutation Hooks

Use `useMutation` with Axios methods. Invalidate related queries on success. Show toast notifications.

```ts
export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateProjectInput) =>
      api.post<Project>("/projects", data).then((res) => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project created");
    },
    onError: () => {
      toast.error("Failed to create project");
    },
  });
};
```

### Mutation patterns by HTTP method

```ts
// Create
mutationFn: (data) => api.post("/projects", data)

// Update
mutationFn: (data) => api.put(`/projects/${id}`, data)

// Partial update
mutationFn: (data) => api.patch(`/projects/${id}`, data)

// Delete
mutationFn: (id: string) => api.delete(`/projects/${id}`)
```

## QueryClient Setup

Create a shared `getQueryClient()` at `lib/get-query-client.ts`. On the server it returns a new client per request; on the browser it returns a singleton.

```ts
import {
  isServer,
  QueryClient,
  defaultShouldDehydrateQuery,
} from "@tanstack/react-query";

function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
      },
      dehydrate: {
        shouldDehydrateQuery: (query) =>
          defaultShouldDehydrateQuery(query) ||
          query.state.status === "pending",
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

export function getQueryClient() {
  if (isServer) {
    return makeQueryClient();
  } else {
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}
```

## Server-Side Prefetching

Prefetch data on the server to avoid client-side loading waterfalls.

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

### Hydration in `page.tsx`

```tsx
import { HydrationBoundary } from "@tanstack/react-query";

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

The `HydrationBoundary` passes server-fetched data to the client `QueryClient`. When `useSuspenseQuery` runs on the client, it finds cached data and renders immediately — no refetch.

## Key Rules

- Use `getQueryClient()` from `lib/get-query-client.ts` — never `new QueryClient()` directly
- Always use `api` from `lib/api.ts` — never raw `axios` or `fetch`
- Export query options functions for reuse in both hooks and `prefetch.ts`
- Use `useSuspenseQuery` (not `useQuery`) for server-hydrated data
- Invalidate queries on mutation success — don't manually update the cache
- Toast on success and error in mutation hooks
