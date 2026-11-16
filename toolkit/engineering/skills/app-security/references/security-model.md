# SECURITY_MODEL.md

Read when the user wants the boundary map kept, or when a repo already has one.

When the user wants the map kept, write the boundary map (law 1) as a `SECURITY_MODEL.md` at the repo
root (or beside a component with its own boundary) — never in `SECURITY.md`, which GitHub treats
as the disclosure policy. It holds exposure, trust boundaries, invariants with stable IDs
(`INV-1`…) and the code that enforces each, reportable finding classes with severity context,
and narrow exclusions (a class plus a location, accepted risks with a review-by date). Later
reviews read it from the base branch, cite invariant IDs in findings, and treat edits to it in a
diff as a gate change. Anything that suppresses or downgrades findings is a decision only the
owner can confirm; leave it marked unresolved otherwise. Suspected gaps go to the user, never into
the file, or later reviews learn to skip them.
