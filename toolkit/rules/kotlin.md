---
paths:
  - "**/*.kt"
  - "**/*.kts"
---
# Kotlin / Android traps

- Never swallow `CancellationException` in a coroutine: `runCatching` and `catch (e: Exception)`
  catch it too, so rethrow it first or cancellation stops propagating.
- targetSdk 35 makes the app edge-to-edge on Android 15: call `enableEdgeToEdge()`, apply insets
  once (Scaffold's `innerPadding`), and set `adjustResize` on activities with a keyboard.
- `EncryptedSharedPreferences` (security-crypto) is deprecated since 1.1.0-alpha07; encrypt
  tokens with an Android Keystore key, never plain SharedPreferences or DataStore.
