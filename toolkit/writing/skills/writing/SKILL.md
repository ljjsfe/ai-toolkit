---
name: writing
description: >-
  Write posts, articles, and social content (X, LinkedIn, 公众号, tech blogs) in the writer's voice
  with zero invented facts ([NEED: ...] placeholders, competing openings, platform rules, de-AI
  editing pass, fresh-reader check). Trigger on 写文章, 发帖, 公众号, 推文, 写稿. Not for resumes
  (career-navigator) or AGENTS.md/CLAUDE.md (agent-instructions).
version: 1.5.0
sources:
  - upstream/khazix-skills/khazix-writer (MIT) — first-hand observation is what a model cannot supply; ask the writer for it [port "first-hand detail comes from the writer"]
  - upstream/marketingskills/skills/copywriting/references/ai-tells.md (MIT) — placeholder for missing proof instead of an invented fact; the swap test [port "never fill it with something" "apply the swap test"]
  - upstream/marketingskills/skills/copywriting/references/ai-tells.md (MIT) — second-generation tells and the writer behind the copy (uneven density, honest limits, never invent experience); persona-built opinions replaced by asking the writer [port "sentences shaped like wisdom" "reflexive specificity" "too balanced" "uneven density" "honest limits" "never invent experience"]
  - upstream/ahao-writing-dna-distiller (MIT) — voice as ranges and verbatim samples by function, not averages; prescriptive rules over descriptions [port "ranges, not averages" "verbatim samples grouped by job" "rules written as instructions"]
  - upstream/ahao-writing-dna-distiller (MIT) — the measuring pipeline (distill_metrics.py for sentence-length spread, short/long ratio, punctuation, nominalisation and risky-word density), beat sheets and structure archetypes, the form-vs-content forbidden map, the AI-flavour firewall self-check [port "sentence-length spread" "def doc_metrics" "that sequence is a structure archetype" "content goes in a forbidden map" "ai-flavour self-check (run after the de-ai pass)"]
  - upstream/everything-claude-code/skills/brand-voice (MIT) — a banned move must be observed in the writer's own corpus; report splits instead of averaging [port "only bans that the corpus shows" "splits, not blends"]
  - upstream/mattpocock-skills/skills/in-progress/writing-shape (MIT) — 2–3 openings, each implying a different thesis; ground a concept before leaning on it [port "draft 2–3 openings, each implying a different thesis" "must be introduced before a sentence leans on it"]
  - upstream/getsentry-skills/skills/blog-writing-guide (Apache-2.0) — open on the problem or the conclusion; voice throughout, not only at the ends; informative headings; name what was not chosen [port "opens on the problem or the conclusion" "not only the first and last paragraph" "say what was not chosen and why"]
  - upstream/marketingskills/skills/social/references/{platforms.md,x-algorithm.md} (MIT) — specific claim at the top of a post; no engagement bait; verified versus reported platform mechanics [port "the first line carries a specific claim" "never a request for likes" "treat reach advice as directional"]
  - upstream/xbtlin-ai-berkshire/codex-skills/wechat-article (MIT) — every formula or number gets a plain-language gloss; when editor and reader disagree, the reader wins [port "gets a plain-language gloss" "change the text for the reader"]
  - upstream/anthropics-skills/skills/doc-coauthoring (licence not stated for this skill; method only) — test the draft on a fresh agent that sees only the draft [port "give a subagent only the draft"]
---

# Writing

A model writes fluent prose unprompted. What it gets wrong is **whose** prose it is and **what
it is allowed to claim**. This skill fixes those two things and runs a de-AI line-editing pass
(`humanizer` / `humanizer-zh`, vendored with the toolkit) followed by checks for what it misses.

## Iron laws

1. **Claim only what a source or the writer gave you.** A missing number, quote, result or
   example becomes `[NEED: what is missing]` in the draft. Never fill it with something
   plausible.
2. **First-hand detail comes from the writer.** What they saw, built, measured or got wrong is
   the part readers trust and the part a model cannot produce. Ask for it in one batch before
   drafting; leave a `[NEED: ...]` where the answer is missing.
3. **The writer's voice beats the defaults.** If a voice profile exists (`PERSONAL.md` in this
   folder), it overrides every style rule below, including the humanizers' rules.
4. **A reader who did not write it gets the last word on clarity.** Where the editing pass and
   the fresh reader disagree, change the text for the reader. On style, law 3 wins: fix what
   confused the reader in the writer's voice.

## Workflow

1. **Frame** — in one line each: who reads it, where it appears, and the one thing they should
   believe or do afterwards. List what the reader already knows; any other concept must be
   introduced before a sentence leans on it.
2. **Gather** — the writer's notes and sources, plus the first-hand questions (law 2). Pull out
   3–7 standalone claims; one piece argues one of them.
3. **Openings** — draft 2–3 openings, each implying a different thesis, and let the writer pick
   or merge. Each opens on the problem or the conclusion, not on background.
4. **Draft** to the platform contract below. Headings, where used, say what the section
   concludes. When the piece argues for a choice, say what was not chosen and why.
5. **Cut** — apply the swap test: a sentence that would read the same on a competitor's or a
   stranger's page says nothing about this writer or this subject; make it specific or delete it.
6. **De-AI** — run `humanizer` (English) or `humanizer-zh` (Chinese) on the cut draft with
   `PERSONAL.md` as the voice sample, then run
   `scripts/new_specifics.py <cut draft> <humanized> --sources <notes…>`: humanizer 4+ adds "a
   specific detail it knows to be true" where text is generic, which law 1 forbids. Every number,
   date, name or quote it lists is traced to the writer or a source, or reverted, or becomes
   `[NEED: …]`. Then check what a pattern pass misses:
   - Scan for the tells that survive a first pass — sentences shaped like wisdom,
     self-narration, tidy closers, staccato bursts, perfect balance between sections,
     reflexive specificity — and, without a profile, ask the writer where the piece should
     be uneven; when a cleaned draft still reads as generated or sounds like nobody, first
     read `references/second-pass-tells.md` (the table and the questions);
   - Confirm against the cut draft that every fact, number, quote, condition, epistemic hedge
     (`may`, `reported`, `可能`, `据称`), the `PERSONAL.md` voice rules, and every `[NEED: ...]`
     marker survived verbatim.
   With a profile in place, also run `scripts/voice_metrics.py <corpus> --draft <draft>` and
   the self-check list in the profile; fix or justify each flag.
7. **Fresh-reader test** — give a subagent only the draft and 3–5 questions the piece must
   answer (what is the claim, why believe it, what should I do). Wrong or hesitant answers mark
   the passages to fix. Without subagents (e.g. some Codex setups), paste the draft alone into a
   fresh session and ask the same questions.

## Platform contracts

| platform | contract |
|---|---|
| X | The first line carries a specific claim and names the topic. One idea per post; a thread only when each post stands alone. End on the point or a question you actually want answered — never a request for likes or agreement. |
| LinkedIn | The text before "see more" (roughly the first 140 characters on mobile) must earn the click with a specific situation or result. Same ending rule as X. |
| WeChat 公众号 | Every formula, number or term gets a plain-language gloss right after it. Keep one analogy through the piece rather than switching. End on a judgement the reader could quote. |
| Technical blog | The opening states the problem or the result within two sentences. The writer's voice runs through the whole piece, not only the first and last paragraph. Show the code, number or diagram behind each claim. |

Platform mechanics change; treat reach advice as directional and say so.

## Voice profile (once per writer)

Built from 3–10 pieces the writer actually published, stored in `toolkit/writing/personal.local.md`
(or `personal/writing.md` in a private copy of the repo) and installed as `PERSONAL.md`:

- **Ranges, not averages** — sentence and paragraph length, as observed spans.
- **Verbatim samples grouped by job** — how they open, turn, give evidence and close, quoted.
- **Rules written as instructions** ("open with the number, then the consequence"), because a
  description of a style does not reliably change output.
- **Only bans that the corpus shows** — something the writer never does, with the evidence.
- **Splits, not blends** — where Chinese and English pieces, or posts and long-form, differ, keep
  both and say which applies where.
- **Measured, then instructed** — `scripts/voice_metrics.py <corpus folder>` gives per-language
  min / median / max for sentence-length spread, short/long share, punctuation, stock-phrase,
  contrast and nominalisation density; each range becomes an instruction in the profile, and
  `--draft draft.md` flags where a draft leaves the range. When building or
  refreshing the profile, or when a draft reads as AI and the profile cannot say why, first
  read `references/voice-distilling.md` (beat sheets and structure archetypes, the forbidden
  map of the writer's own cases and lines, a writer-specific AI-flavour self-check).

## Output

```
Draft:      the piece, with every [NEED: ...] left visible
Questions:  the first-hand details still missing
Checks:     the claims list (each with its source), the cut, and the fresh-reader answers
```
