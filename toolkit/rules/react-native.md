---
paths:
  - "**/app.json"
  - "**/app.config.*"
  - "**/eas.json"
  - "**/metro.config.*"
  - "**/*.ios.tsx"
  - "**/*.android.tsx"
  - "**/*.native.tsx"
---
# React Native / Expo traps

- An OTA (EAS) update carries only JS and assets; native code, config, libraries
  and SDK upgrades need a new build. Never work around a runtime-version mismatch.
- Never change the runtime-version policy as an incidental fix; it decides which builds get
  updates.
- `EXPO_PUBLIC_*` variables are inlined into the client bundle: no secrets in them.
- Tokens go in `expo-secure-store`, never AsyncStorage.
- Expo Go runs only the native modules it bundles; others need a development build
  (`expo-dev-client`).
