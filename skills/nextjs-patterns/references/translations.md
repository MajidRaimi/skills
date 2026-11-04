# Translations

Tolgee for i18n — setup files, server/client translation functions, language switching, static JSON messages.

## File Structure

```
src/
├── lib/tolgee/
│   ├── shared.ts       # Tolgee instance factory + config
│   ├── language.ts      # Server actions for language cookie
│   ├── client.tsx       # TolgeeNextProvider (client wrapper)
│   └── server.tsx       # Server-side getTranslate, T component
├── messages/
│   ├── en.json          # English translations
│   └── fr.json          # French translations (one file per language)
```

| File | Purpose |
|------|---------|
| `lib/tolgee/shared.ts` | Base Tolgee instance with plugins, languages, RTL list, static data |
| `lib/tolgee/language.ts` | `getLanguage()` / `setLanguage()` / `getDirection()` via cookies |
| `lib/tolgee/client.tsx` | `TolgeeNextProvider`, `useDirection()` hook |
| `lib/tolgee/server.tsx` | `getTranslate`, `getTolgee`, `T` for server components |

> `lib/tolgee/` (not `src/tolgee/`) — the skill places external integrations in `lib/`.

## Setup Files

### `lib/tolgee/shared.ts`

```ts
import { FormatSimple, Tolgee, DevTools } from "@tolgee/web";
import enMessages from "@/messages/en.json";
import frMessages from "@/messages/fr.json";

export const ALL_LANGUAGES = ["en", "fr"] as const;
export const DEFAULT_LANGUAGE = "en";
export const RTL_LANGUAGES = ["ar", "fa"];

export function TolgeeBase() {
  return Tolgee()
    .use(FormatSimple())
    .use(DevTools())
    .init({
      defaultLanguage: DEFAULT_LANGUAGE,
      availableLanguages: ALL_LANGUAGES as unknown as string[],
      apiKey: process.env.NEXT_PUBLIC_TOLGEE_API_KEY,
      apiUrl: process.env.NEXT_PUBLIC_TOLGEE_API_URL,
      staticData: { en: enMessages, fr: frMessages },
    });
}
```

### `lib/tolgee/language.ts`

```ts
"use server";

import { cookies, headers } from "next/headers";
import { ALL_LANGUAGES, DEFAULT_LANGUAGE, RTL_LANGUAGES } from "./shared";

const LANGUAGE_COOKIE = "NEXT_LOCALE";

export async function getLanguage(): Promise<string> {
  const cookieStore = await cookies();
  const stored = cookieStore.get(LANGUAGE_COOKIE)?.value;
  if (stored && ALL_LANGUAGES.includes(stored as (typeof ALL_LANGUAGES)[number])) {
    return stored;
  }
  const acceptLanguage = (await headers()).get("accept-language") ?? "";
  const preferred = acceptLanguage.split(",")[0]?.split("-")[0];
  if (preferred && ALL_LANGUAGES.includes(preferred as (typeof ALL_LANGUAGES)[number])) {
    return preferred;
  }
  return DEFAULT_LANGUAGE;
}

export async function setLanguage(lang: string) {
  const cookieStore = await cookies();
  cookieStore.set(LANGUAGE_COOKIE, lang, { path: "/", maxAge: 60 * 60 * 24 * 365 });
}

export async function getDirection() {
  const language = await getLanguage();
  return RTL_LANGUAGES.includes(language) ? "rtl" : "ltr";
}
```

### `lib/tolgee/client.tsx`

```tsx
"use client";

import { useRouter } from "next/navigation";
import { useTolgee, TolgeeProvider, TolgeeStaticData } from "@tolgee/react";
import { TolgeeBase, RTL_LANGUAGES } from "./shared";

type Props = {
  language: string;
  staticData: TolgeeStaticData;
  children: React.ReactNode;
};

const tolgee = TolgeeBase().init();

export function TolgeeNextProvider({ language, staticData, children }: Props) {
  const router = useRouter();
  return (
    <TolgeeProvider
      tolgee={tolgee}
      options={{ useSuspense: false }}
      language={language}
      staticData={staticData}
      ssr={{ onLanguageChange(lang) { router.refresh(); } }}
    >
      {children}
    </TolgeeProvider>
  );
}

export function useDirection() {
  const tolgee = useTolgee(["language"]);
  const language = tolgee.getLanguage();
  return RTL_LANGUAGES.includes(language ?? "en") ? "rtl" : "ltr";
}
```

### `lib/tolgee/server.tsx`

```tsx
import { createServerInstance } from "@tolgee/react/server";
import { TolgeeBase } from "./shared";
import { getLanguage } from "./language";

const { getTolgee, getTranslate, T } = createServerInstance({
  getLocale: getLanguage,
  createTolgee: async (language) => TolgeeBase().init({ language }),
});

export { getTolgee, getTranslate, T };
```

## Translation Files

`messages/en.json`:
```json
{
  "projects_title": "Projects",
  "project_count": "You have {count} projects"
}
```
One JSON file per language. Keys are flat strings — use `{param}` for interpolation.

## Provider Integration

Wrap children with `TolgeeNextProvider` in `app/layout.tsx`:
```tsx
import { DirectionProvider } from "@/components/ui/direction";
import { getLanguage, getDirection } from "@/lib/tolgee/language";
import { getStaticData } from "@/lib/tolgee/server";
import { TolgeeNextProvider } from "@/lib/tolgee/client";

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const language = await getLanguage();
  const direction = await getDirection();
  const staticData = await getStaticData();
  return (
    <html lang={language} dir={direction}>
      <body>
        <DirectionProvider direction={direction}>
          <RootProvider>
            <TolgeeNextProvider language={language} staticData={staticData}>
              {children}
            </TolgeeNextProvider>
          </RootProvider>
        </DirectionProvider>
      </body>
    </html>
  );
}
```

> `TolgeeNextProvider` lives in `layout.tsx` (not `root-provider.tsx`) because it needs async server-resolved props that cannot be resolved inside a `"use client"` component.

See [Components & State](components-and-state.md) for the provider composition pattern. See [shadcn/ui](shadcn-ui.md) for `DirectionProvider` details.

## Server Translations

```tsx
import { getTranslate } from "@/lib/tolgee/server";

export default async function ProjectsPage() {
  const t = await getTranslate();
  return <h1>{t("projects_title")}</h1>;
}
```

## Client Translations

**`useTranslate` hook:**
```tsx
"use client";
import { useTranslate } from "@tolgee/react";

export function ProjectCount({ count }: { count: number }) {
  const { t } = useTranslate();
  return <p>{t("project_count", { count })}</p>;
}
```

**`T` component:**
```tsx
import { T } from "@tolgee/react";

<T keyName="project_count" params={{ count: 5 }} />
```

## Language Switching

```tsx
"use client";
import { useTolgee } from "@tolgee/react";
import { setLanguage } from "@/lib/tolgee/language";
import { ALL_LANGUAGES } from "@/lib/tolgee/shared";

export function LanguageSwitcher() {
  const tolgee = useTolgee(["language"]);
  const currentLang = tolgee.getLanguage();
  return (
    <select value={currentLang} onChange={(e) => setLanguage(e.target.value)}>
      {ALL_LANGUAGES.map((lang) => (
        <option key={lang} value={lang}>{lang}</option>
      ))}
    </select>
  );
}
```

## Direction (RTL / LTR)

**Server** — use `getDirection()` from `language.ts` (e.g. in `layout.tsx` for `<html dir>` and `DirectionProvider`):
```tsx
import { DirectionProvider } from "@/components/ui/direction";
import { getLanguage, getDirection } from "@/lib/tolgee/language";

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const language = await getLanguage();
  const direction = await getDirection();
  return (
    <html lang={language} dir={direction}>
      <body>
        <DirectionProvider direction={direction}>...</DirectionProvider>
      </body>
    </html>
  );
}
```

**Client** — use `useDirection()` from `client.tsx`:
```tsx
import { useDirection } from "@/lib/tolgee/client";

export function MyComponent() {
  const dir = useDirection();
  return <div dir={dir}>...</div>;
}
```

## API Quick Reference

| API | Context | Usage |
|-----|---------|-------|
| `getTranslate()` | Server | `const t = await getTranslate(); t("key")` |
| `useTranslate()` | Client | `const { t } = useTranslate(); t("key")` |
| `T` component | Client | `<T keyName="key" params={{}} />` |
| `useTolgee(events)` | Client | `const tolgee = useTolgee(["language"])` |
| `setLanguage(lang)` | Server action | Cookie-based language persistence |
| `getLanguage()` | Server | Read current language from cookie/headers |
| `getDirection()` | Server | `const dir = await getDirection()` → `"rtl"` or `"ltr"` |
| `useDirection()` | Client | `const dir = useDirection()` → `"rtl"` or `"ltr"` |

## Environment Variables

```
NEXT_PUBLIC_TOLGEE_API_KEY=your-api-key
NEXT_PUBLIC_TOLGEE_API_URL=https://app.tolgee.io
```

> The API key enables in-context editing in development. Omit in production — Tolgee falls back to static JSON files.
