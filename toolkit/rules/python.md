---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---
# Python traps

- `asyncio.TaskGroup` raises an `ExceptionGroup`. A plain `except ValueError:` around the
  `async with TaskGroup()` block never matches; use `except* ValueError:`.
- Check `requires-python` before using modern typing features: PEP 695 syntax (`type Alias = ...`,
  `def first[T](xs: list[T]) -> T`, `class Box[T]:`) and `typing.override` require Python 3.12+;
  `warnings.deprecated` requires Python 3.13+ (use `typing_extensions.deprecated` on <3.13).
