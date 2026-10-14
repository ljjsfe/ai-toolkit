---
paths:
  - "**/*.dart"
  - "**/pubspec.yaml"
---
# Flutter / Dart traps

- After every `await` in a widget, check `if (!context.mounted) return;` (or `mounted` in a
  `State`) before using `context`, calling `setState`, navigating or showing a snackbar.
- Token-refresh interceptors (Dio and similar) must mark the retried request and never refresh
  twice for it; otherwise a failed refresh loops 401 → refresh → 401.
- Dart macros were cancelled (January 2025) and will not ship. Use `build_runner` code
  generation (freezed, json_serializable) or plain records and pattern matching.
- Dart 3: prefer records, patterns, `switch` expressions and `sealed` classes for state over
  boolean flags; exhaustive switches need no `default`.
- Cancel every manual `StreamSubscription`, controller and timer in `dispose()`.
