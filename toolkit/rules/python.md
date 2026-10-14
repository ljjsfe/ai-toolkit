---
paths:
  - "**/*.py"
  - "**/pyproject.toml"
---
# Python traps

- `asyncio.TaskGroup` raises an `ExceptionGroup`. A plain `except ValueError:` around the
  `async with TaskGroup()` block never matches; use `except* ValueError:`.
- On Python 3.12+, prefer PEP 695 syntax (`type Alias = ...`, `def first[T](xs: list[T]) -> T`,
  `class Box[T]:`) and `typing.override`; on 3.13+, `warnings.deprecated` / `typing_extensions`
  for deprecations. Check `requires-python` before using them.
