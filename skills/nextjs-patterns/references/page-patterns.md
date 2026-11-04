# Page Patterns

Server component pages, prefetching, Suspense boundaries, fallbacks, and layouts.

## Server Component Page

Every route's `page.tsx` is a server component with logic only — it parses params, prefetches data, and composes providers. It imports sections or components but never contains UI markup itself.

```tsx
import { Suspense } from "react";
import { HydrationBoundary } from "@tanstack/react-query";
import type { SearchParams } from "nuqs/server";
import { loadProjectsParams } from "./params";
import { prefetchProjects } from "./prefetch";
import { ProjectsView } from "./_components/projects-view";
import { ProjectsFallback } from "./fallback";

type PageProps = { searchParams: Promise<SearchParams> };

export default async function ProjectsPage({ searchParams }: PageProps) {
  // 1. Parse search params on the server
  const params = await loadProjectsParams(searchParams);

  // 2. Prefetch data and dehydrate
  const dehydratedState = await prefetchProjects(params);

  // 3. Wrap client component with hydration + suspense
  return (
    <HydrationBoundary state={dehydratedState}>
      <Suspense fallback={<ProjectsFallback />}>
        <ProjectsView />
      </Suspense>
    </HydrationBoundary>
  );
}
```

### Flow

1. **Parse** — `loadProjectsParams` extracts typed params from the URL
2. **Prefetch** — `prefetchProjects` runs the query on the server, returns dehydrated state
3. **Hydrate** — `HydrationBoundary` passes cached data to the client QueryClient
4. **Suspend** — `Suspense` shows the fallback while the client component resolves
5. **Render** — `ProjectsView` calls `useSuspenseQuery`, finds cached data, renders instantly

## Prefetch Function

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

### Multiple Prefetches

When a page needs multiple queries, prefetch them in parallel:

```ts
import { dehydrate } from "@tanstack/react-query";
import { getQueryClient } from "@/lib/get-query-client";

export const prefetchProjectDetail = async (id: string) => {
  const queryClient = getQueryClient();

  await Promise.all([
    queryClient.prefetchQuery(projectQueryOptions(id)),
    queryClient.prefetchQuery(projectTasksQueryOptions(id)),
  ]);

  return dehydrate(queryClient);
};
```

## Fallback Components

### Loading Fallback (Skeleton)

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

### Empty State

```tsx
import { EmptyState } from "@/components/custom/empty-state";

export const ProjectsEmpty = () => (
  <EmptyState
    title="No projects yet"
    description="Create your first project to get started."
    action={{ label: "Create Project", onClick: () => {} }}
  />
);
```

Use empty state inside the client container:

```tsx
const { data } = useProjects();
if (data.data.length === 0) return <ProjectsEmpty />;
```

## Suspense Boundary Placement

Place `<Suspense>` around each independently loading section:

```tsx
// Single data source — one boundary
<Suspense fallback={<ProjectsFallback />}>
  <ProjectsView />
</Suspense>

// Multiple independent sections — separate boundaries
<div className="grid grid-cols-2 gap-4">
  <Suspense fallback={<StatsFallback />}>
    <StatsPanel />
  </Suspense>
  <Suspense fallback={<ActivityFallback />}>
    <ActivityFeed />
  </Suspense>
</div>
```

> Each Suspense boundary loads independently — one section doesn't block another.

## Detail Page Pattern

For pages with a dynamic `[id]` param:

```tsx
// app/(dashboard)/projects/[id]/page.tsx
import { Suspense } from "react";
import { HydrationBoundary } from "@tanstack/react-query";
import { prefetchProjectDetail } from "./prefetch";
import { ProjectDetail } from "./_components/project-detail";
import { ProjectDetailFallback } from "./fallback";

type PageProps = { params: Promise<{ id: string }> };

export default async function ProjectPage({ params }: PageProps) {
  const { id } = await params;
  const dehydratedState = await prefetchProjectDetail(id);

  return (
    <HydrationBoundary state={dehydratedState}>
      <Suspense fallback={<ProjectDetailFallback />}>
        <ProjectDetail id={id} />
      </Suspense>
    </HydrationBoundary>
  );
}
```

## Layout Pattern

Layouts wrap child routes and persist across navigations.

```tsx
// app/(dashboard)/layout.tsx
import { Sidebar } from "@/components/custom/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  );
}
```

## Section-Based Pages

Large pages (landing, marketing) use a `_sections/` folder to organize distinct visual blocks. Sections are server components by default — only add `"use client"` on small interactive parts within them.

```
app/(marketing)/
├── page.tsx
└── _sections/
    ├── hero.tsx
    ├── features.tsx
    └── cta.tsx
```

### `page.tsx`

```tsx
import { Hero } from "./_sections/hero";
import { Features } from "./_sections/features";
import { CTA } from "./_sections/cta";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Features />
      <CTA />
    </>
  );
}
```

> `_sections/` is optional — only for pages with distinct visual blocks. Data-driven pages use `_components/` with the Suspense pattern above.

The root layout includes `RootProvider` (see [Components & State](components-and-state.md)).
