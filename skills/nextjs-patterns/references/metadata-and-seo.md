# Metadata & SEO

Dynamic metadata with `generateMetadata`, static metadata exports, and OG image generation.

## Static Metadata

Export a `metadata` object from any `page.tsx` or `layout.tsx`. Layout metadata is inherited by all child pages; page metadata overrides layout metadata.

```tsx
// app/(dashboard)/projects/layout.tsx
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Projects",
  description: "Manage your projects",
};
```

## Dynamic Metadata (generateMetadata)

Use an async `generateMetadata` function when metadata depends on data. Uses our Axios `api` instance (consistent with "No fetch" rule).

```tsx
// app/(dashboard)/projects/[id]/page.tsx
import type { Metadata } from "next";
import { api } from "@/lib/api";

type Props = { params: Promise<{ id: string }> };

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const project = await api
    .get<Project>(`/projects/${id}`)
    .then((res) => res.data);

  return {
    title: project.name,
    description: project.description,
    openGraph: {
      title: project.name,
      description: project.description,
    },
  };
}
```

- `generateMetadata` runs on the server before the page renders — it blocks streaming until resolved
- Next.js automatically deduplicates `fetch` requests, but since we use Axios, the same API call in `generateMetadata` and `prefetch` will run twice. Keep metadata fetches lightweight or accept the duplication.
- Cross-ref → [Page Patterns](page-patterns.md) for the full `page.tsx` structure (`generateMetadata` sits alongside the default export)

## Metadata Merging

Metadata flows from root layout → nested layout → page. Child metadata overrides parent for same fields.

Use `title.template` in the root layout for consistent page title formatting:

```tsx
// app/layout.tsx
export const metadata: Metadata = {
  title: { default: "My App", template: "%s | My App" },
  description: "My application",
};
```

Result: a page with `title: "Projects"` renders as `"Projects | My App"`.

## OG Image Generation

Use the `opengraph-image.tsx` file convention with `ImageResponse` for dynamic OG images.

```tsx
// app/(dashboard)/projects/[id]/opengraph-image.tsx
import { ImageResponse } from "next/og";
import { api } from "@/lib/api";

export const runtime = "edge";
export const alt = "Project";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default async function Image({
  params,
}: {
  params: { id: string };
}) {
  const project = await api
    .get<Project>(`/projects/${params.id}`)
    .then((res) => res.data);

  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          width: "100%",
          height: "100%",
          backgroundColor: "#000",
          color: "#fff",
          fontSize: 48,
        }}
      >
        <div>{project.name}</div>
        <div style={{ fontSize: 24, color: "#888" }}>
          {project.description}
        </div>
      </div>
    ),
    { ...size },
  );
}
```

- File must be named `opengraph-image.tsx` (Next.js convention) — Next.js auto-discovers it and adds the `og:image` meta tag
- Use `twitter-image.tsx` for Twitter cards (same API)

## File Placement

| File | Location | Purpose |
|------|----------|---------|
| Static metadata | `export const metadata` in any page/layout | Title, description, icons |
| `generateMetadata` | Same file as `page.tsx` | Data-driven metadata |
| `opengraph-image.tsx` | Same directory as `page.tsx` | Dynamic OG images |
| `twitter-image.tsx` | Same directory as `page.tsx` | Dynamic Twitter cards |
| `icon.tsx` | `app/icon.tsx` | Dynamic favicon |
| `sitemap.ts` | `app/sitemap.ts` | Generated sitemap |
| `robots.ts` | `app/robots.ts` | Generated robots.txt |

## Key Rules

- Use static `metadata` export for pages with fixed content; use `generateMetadata` when metadata depends on data
- Use `api` instance from `lib/api.ts` for data fetching inside `generateMetadata` — never raw `fetch`
- `generateMetadata` blocks rendering — keep the data fetch lightweight
- Place `opengraph-image.tsx` in the same route segment as the page it serves
- Use `title.template` in root layout for consistent page title formatting
