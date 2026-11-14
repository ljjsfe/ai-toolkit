# Case design for special shapes

Read this when the eval targets a tool server's question answering, a skill that other skills
or standing instructions call, or a skill or tool's trigger description, or when a pilot passes
every run.

## Question-answering evals of a tool server

Each question must be answerable with read-only operations; not solvable by keyword search
(paraphrase, don't quote); stable over time (never "the current count"); and resolved to a
single string that can be compared exactly.

## Skills invoked by callers

A skill that other skills or standing instructions invoke is tested the way it is called. The
task text is what the caller passes (a mode token, a scope, one line of context), not a user's
request — a loose task invites extra work and the eval then measures the task text. Grade
overreach as well as the intended result: fail runs that edit outside the scope, commit, or add
files nobody asked for. Put pre-existing items inside the files the work touches, or a "change
only the current work" rule passes trivially.

## Tuning when a skill or tool triggers

Collect should-trigger and should-not-trigger prompts; split them 60/40; revise the description
from failures on the 60; choose the final wording by the score on the 40; run each prompt more
than once, because routing is noisy.

## The all-pass pilot

ECC's GateGuard pilot is the example of a ceiling: 72 sessions across four arms, every one
passed, so its hypotheses stayed untested rather than refuted. With no variance there is
nothing to compare; redesign the tasks so they can fail before reading cost or turn
differences.
