---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.mjs"
  - "**/next.config.*"
  - "**/tsconfig*.json"
---
# TypeScript, React and Next.js traps

Check `package.json` versions first; if `node_modules/next/dist/docs/` exists (Next.js 16.3+),
read the version-matched docs there before guessing Next 16+ APIs.

**TypeScript**
- `strict: true` does not enable `noUncheckedIndexedAccess` or `exactOptionalPropertyTypes`.
  Check the tsconfig before assuming indexed access is safe or that `undefined` may be assigned
  to optional properties.
- Conditional types distribute over unions: `T extends X ? A : B` maps each member. Wrap as
  `[T] extends [X]` to stop it.
- `moduleResolution: "node"` is the legacy mode; modern projects use `"bundler"` or
  `"nodenext"` — match the toolchain.

**React 19 & RSC**
- `useActionState(action, initialState, permalink?)` (from `react`) replaces `useFormState`
  (from `react-dom`) and returns `[state, formAction, isPending]`; the action itself receives
  `(prevState, formData)`.
- Pass Server Components into `"use client"` wrappers via `children` or JSX slot props — never
  via `renderX={() => <ServerChild />}` functions, which break RSC serialization or pull the tree
  into the client bundle.
- Deduplicate non-`fetch` server DB/SDK reads shared across layout and page RSCs in one request
  with `React.cache()`.
- If the project uses React Compiler, do not add manual `useMemo` / `useCallback` /
  `React.memo` for performance; check the build config first.
- `suppressHydrationWarning` goes on the exact element whose content differs (a timestamp), never
  on a container — it hides real mismatches below it.

**Next.js**
- Next 15+: `fetch` is **not cached by default** and GET route handlers are dynamic by default.
  Opt in to caching explicitly; Next 16 replaces `unstable_cache` with `"use cache"` + `cacheLife`
  + `cacheTag`.
- Next 16: `middleware.ts` is renamed `proxy.ts` (export `proxy`), and it runs on the Node.js
  runtime. Do not "fix" `proxy.ts` back to `middleware.ts`.
- Defer non-blocking post-response work (analytics, audit logs) with `after()` from `next/server`
  instead of `await`ing inline before returning.
- Server Actions are public HTTP endpoints. Authenticate and authorise inside every
  `"use server"` function; a hidden or disabled button is not access control.
- Any cache (`"use cache"`, `unstable_cache`, CDN, `fetch` cache) must key on every input the
  response varies on — user, tenant, locale, permissions — or one user's data is served to another.
