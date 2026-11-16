---
paths:
  - "**/*.swift"
---
# Swift / SwiftUI traps

- Xcode is silent on soft-deprecated SwiftUI APIs: a warning-free build does not prove current
  APIs. Check the symbol's `@available`.
- Check the deployment target before using a newer API; otherwise gate it with `#available`.
  Never raise the target.
- View-owned `@State` must be `private`: with Xcode 27's `@State` macro, a non-private initial
  expression re-runs on every parent rebuild.
- `@AppStorage` inside an `@Observable` class never triggers view updates, even with
  `@ObservationIgnored`.
- `ForEach`/`List` row identity comes from the element, never indices or `\.offset`.
- SwiftData with CloudKit: no `@Attribute(.unique)`; every property optional or defaulted, every
  relationship optional.
- Tokens and passwords go in the Keychain, never `@AppStorage`/UserDefaults.
