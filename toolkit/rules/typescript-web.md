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

Check `package.json` versions first; these depend on them.

**TypeScript**
- `strict: true` does not enable `noUncheckedIndexedAccess` or `exactOptionalPropertyTypes`.
  Check the tsconfig before assuming indexed access is safe or that `undefined` may be assigned
  to optional properties.
- Conditional types distribute over unions: `T extends X ? A : B` maps each member. Wrap as
  `[T] extends [X]` to stop it.
- `moduleResolution: "node"` is the legacy mode; modern projects use `"bundler"` or
  `"nodenext"` — match the toolchain.

**React 19**
- `useActionState(action, initialState, permalink?)` (from `react`) replaces `useFormState`
  (from `react-dom`) and returns `[state, formAction, isPending]`; the action itself receives
  `(prevState, formData)`.
- If the project uses React Compiler, do not add manual `useMemo` / `useCallback` /
  `React.memo` for performance; check the build config first.
- `suppressHydrationWarning` goes on the exact element whose content differs (a timestamp), never
  on a container — it hides real mismatches below it.

**Next.js**
- Next 15+: `fetch` is **not cached by default** and GET route handlers are dynamic by default.
  Opt in to caching explicitly.
- Next 16: `middleware.ts` is renamed `proxy.ts` (export `proxy`), and it runs on the Node.js
  runtime. Do not "fix" `proxy.ts` back to `middleware.ts`.
- Server Actions are public HTTP endpoints. Authenticate and authorise inside every
  `"use server"` function; a hidden or disabled button is not access control.
- Any cache (`unstable_cache`, CDN, `fetch` cache) must key on every input the response varies
  on — user, tenant, locale, permissions — or one user's data is served to another.
