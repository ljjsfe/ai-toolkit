# Archive steps

What `spec_check.py merge` performs, and the manual procedure when Python cannot run. Read when
archiving without the script or when a merge precondition fails and you need to know why.

1. For each delta `changes/<slug>/specs/<capability-path>/spec.md`, open or create the living
   `specs/<capability-path>/spec.md` (`# <Capability>`, `## Purpose`, `## Requirements`). When
   creating a new capability spec, only `## Purpose` + `## ADDED Requirements` are valid.
2. Apply operations in strict order so renames and edits compose without collision:
   - **`RENAMED`** — replace matching `### Requirement:` headers in place. Abort if the source
     is missing or the target already exists.
   - **`REMOVED`** — delete matching requirement blocks. If removing the last requirement retires
     the capability, confirm retirement intent and delete the capability's `spec.md` rather than
     leaving an empty `## Requirements` section.
   - **`MODIFIED`** — replace the entire matching requirement block with the delta's full block.
     Abort if the living block has a scenario the delta block lacks (law 4).
   - **`ADDED`** — append new requirement blocks after checking no duplicate ID or header exists.
   - A header that matches only after ignoring case or spacing is an error, never a match. Plan
     every capability before writing any: one failure means nothing is written.
3. Audit each touched living spec (`spec_check.py audit`): single `## Purpose` and `## Requirements`, zero leftover delta
   headers (`ADDED`/`MODIFIED`/`REMOVED`/`RENAMED`), zero changelog or date annotations, unique
   requirement IDs/headers, and ≥1 `#### Scenario:` (`WHEN`/`THEN`) under every requirement.
4. Move `changes/<slug>/` to `changes/archive/YYYY-MM-DD-<slug>/` (do not double-prefix if `<slug>`
   already starts with `YYYY-MM-DD-`).
