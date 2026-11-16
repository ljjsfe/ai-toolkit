# Distilling a voice profile

Read when building or refreshing `PERSONAL.md` from a writer's published pieces, or when a draft
"sounds like AI" and the profile cannot say why.

## 1. Measure the ranges

Put 3–10 published pieces (more is better, mixed types and periods) as `.md` or `.txt` in one
folder and run `scripts/voice_metrics.py <folder>`. It measures each piece separately, splits
Chinese from English, and reports min / median / max per language for sentence-length spread
(cv), short and long sentence share, paragraph length, punctuation per 1,000 units, stock-AI
phrase density, "not X but Y" density and nominalisation density.

Turn every number into an instruction before it goes in the profile; a number alone changes
nothing in the next draft:

| measured | instruction it becomes |
|---|---|
| short-sentence share 30–45% | at least one sentence of 8 characters (or 6 words) or fewer in every 3–4; one in the first 100 characters |
| cv 0.55–0.80 | no run of three sentences within a few units of each other's length |
| stock-phrase density near 0 | the phrases on the script's list are banned outright for this writer |
| stock-phrase density low but non-zero | the writer's own phrases (the script lists them) allowed up to their observed rate per piece |
| contrast density near 0 | no "not X but Y" / 不是…而是 unless someone in the piece actually claimed X |
| paragraph mean 40–70 | paragraphs under about 1.3 × the observed maximum; one-sentence paragraphs allowed where the writer uses them |
| digit density high | a name or a number in every 2–3 paragraphs; "many", "some", "很多", "一些" replaced |

Then check a draft: `scripts/voice_metrics.py <folder> --draft draft.md` flags a metric only
when it falls outside the writer's range for that language widened by one interquartile range
each side ([min − IQR, max + IQR]); with 3–10 pieces the bare min–max is so narrow that the
writer's own next piece would fail it. A stock phrase is flagged only above the highest rate
the writer used it at in any piece (a phrase they never used is flagged at any rate). Exit 1 means
something to fix or to justify; a range from fewer than three pieces is shown as too thin.

## 2. Structure: beats and archetypes

Chapter labels ("intro, three points, conclusion") do not preserve rhythm; beats do.

- For each piece, copy its first two and last two sentences verbatim, then cut the body into
  beats: one beat per change of function (hook, question, claim, evidence, story, data, turn,
  transition, summary, quotable line, call to action), usually 1–3 paragraphs each and 8–15
  beats in a 2,000–4,000-character piece. Per beat note length, information type and how it
  hands over to the next (question, "but", escalation, example, list).
- Lay beat sheets of similar pieces side by side. Where the function sequence repeats across
  topics, that sequence is a structure archetype. Most writers have 3–5. Record each with a
  name, the topics it is used for, its beat sequence, one representative piece, and its tension
  curve (where it worries the reader and where it releases).
- Write the topic-to-archetype choice down ("a contrarian claim → archetype A; a how-I-did-it →
  archetype C"). It is the entry point when drafting: pick the archetype, then the opening.
- Opening and closing libraries: sort the copied first and last sentences by type (question,
  scene, number; plain stop, quotable line, question to readers). Drafts learn the type and
  write new sentences.

## 3. Form versus content: the forbidden map

Test for each observation: would it still hold on a completely different topic?

- **Form (reusable):** archetypes and beat sequences, sentence rhythm, signature sentence
  shapes, forms of address, rhetorical habits, layout (bold, paragraph length, headings), hook
  type, the way the writer breaks a problem down, the technique of being specific.
- **Content (forbidden to reuse):** topics already written, signature cases and stories,
  proprietary numbers, the writer's original memorable lines verbatim, strong positions tied to
  a topic.

Content goes in a forbidden map in the profile. A new draft checks it: no reused case or
number, no verbatim signature line, a clashing position gets a new angle or a new argument, a
heavily overlapping topic is flagged to the writer. Specificity is form; the specific case the
writer used last time is content.

## 4. AI-flavour self-check (run after the de-AI pass)

Specific to this writer, so build it from steps 1–3:

- [ ] Read aloud: does it sound like a person talking or a report? A report fails.
- [ ] Zero hits on this writer's banned phrases; allowed phrases within their rate.
- [ ] Short sentences at the instructed rate; at least one paragraph that is a single sentence
      if the writer uses them.
- [ ] A real name, number or scene every 2–3 paragraphs.
- [ ] Transitions the writer's way (the profile quotes 3–5 of theirs), not "However /
      Moreover / 然而 / 此外".
- [ ] Verbs, not nominalisations ("cut the build time", not "carried out an optimisation of").
- [ ] The writer's attitude appears somewhere (their particles, their kind of joke or
      complaint), quoted from samples, never invented.
- [ ] The ending is one of the writer's closing types, not an uplifting summary.
- [ ] `voice_metrics.py --draft` exit 0, or every flag has a reason.
- [ ] Forbidden map clean.

Any unticked line goes back to editing, not to the reader.
