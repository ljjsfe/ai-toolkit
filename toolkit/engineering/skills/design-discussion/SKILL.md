---
name: design-discussion
description: "Hold an in-depth design conversation before any plan exists — ask one question at a time with a guess attached, pin the goal, constraints and what \"good\" means before proposing, lay out 2-3 approaches that differ in mechanism, sharpen vague terms, keep a decision log so nothing is re-argued, and stop when no open question would change the design. Use for an open-ended design conversation while the goal and constraints are still unsettled — \"let's discuss the design\", API or data-model options, 讨论方案, 聊设计; once the shape is clear use system-design (sizing, review) or agent-architecture (agent systems)."
version: 1.0.0
sources:
  - upstream/superpowers/skills/brainstorming (MIT) — think wide privately, play back in chunks, builder check by a fresh reader, nothing built before approval
  - upstream/addyosmani-agent-skills/skills/interview-me (MIT) — one question with a guess attached, "want vs should want" probe, predict-the-next-three stop test, bare assent is not a yes
  - upstream/addyosmani-agent-skills/skills/idea-refine (MIT) — directions must differ, not vary; name what each bets on; a not-doing list
  - upstream/mattpocock-skills/skills/engineering/domain-modeling (MIT) — sharpen overloaded terms, edge-case scenarios, check the code, ADR only when hard to reverse, surprising and a real trade-off
  - upstream/mattpocock-skills/skills/engineering/grill-with-docs (MIT) — record decisions and terms as they settle, not at the end
  - upstream/compound-engineering-plugin/skills/ce-brainstorm/references/{approaches,dialogue,interaction-rules,settled-decisions}.md (MIT) — present all approaches before recommending, anti-genericness test, look up rather than ask, integration check, no self-settling of decisions
  - upstream/gstack/office-hours (MIT) — premise challenge (right problem, cost of doing nothing, what already exists); minimal versus long-term versus lateral approaches
---

# Design Discussion

A design conversation is worth having because each answer changes the next question. Treat it
as a dialogue that converges on decisions, not an interview that collects requirements.

## Iron laws

1. **One question per message, with your guess attached.** Ask the single question whose answer
   most changes the design, state what you expect the answer to be and why, then wait. A list of
   questions gets skimmed answers and locks in a framing before the first answer arrives.
2. **No approaches before the frame.** Until the goal, the binding constraints and the test for
   "good" are stated (or recorded as assumptions), do not propose a solution. Before the first
   proposal, ask what the user already has in mind; your framing anchors theirs.
3. **Approaches differ in mechanism, not in parameters.** Two caches with different TTLs are
   one approach. Show all of them before you recommend one.
4. **Keep a decision log and honour it.** A decided item is not re-asked; it reopens only on
   new evidence, which you name. Only the user settles a decision — your own proposal that they
   did not engage with stays *open*, and "sounds good" covers only what you actually showed.
5. **Stop when the next answers would not change the design.** Test: can you predict the
   user's reaction to the next three questions you would ask? If yes, write the doc.
6. **Nothing gets built during the discussion.** Reading code to answer a question is fine;
   scaffolding, installing or writing product code waits for an approved design doc.

## Step 1 — Frame (goal, constraints, "good")

Cover this ground through the one-at-a-time dialogue, never as a checklist read aloud:

| ground | what settles it |
|---|---|
| goal | the outcome in one sentence, and who or what benefits |
| what "good" means | an observable test: a latency, a failure it must survive, a change it must make cheap |
| binding constraints | the one or two that actually bind (team, existing system, deadline, cost) |
| non-goals | what this deliberately will not do — make it explicit; it is where misalignment hides |
| premise | is this the right problem? what happens if nothing is built? what already partly does it? |

- **Look it up instead of asking** when the codebase or docs can answer; ask the user only for
  decisions and preferences. When the user states how the system works, check the code and raise
  any contradiction before building on it.
- **Probe "should want" answers.** When a goal arrives as a virtue word (scalable, clean,
  flexible, robust), ask what concrete situation it must handle; if it sounds like justifying to
  an imagined reviewer, ask what they would want with no one to justify it to.

## Step 2 — Sharpen the language

Vague terms hide undecided design. Whenever one is load-bearing, stop and pin it.

- **Overloaded nouns:** "you say *account* — the paying organisation or the person logging in?"
  Propose one precise term per concept and use it from then on.
- **Boundary scenarios:** invent a concrete edge case that forces a choice — a partial refund, a
  retried webhook, an agent that times out mid-tool-call — and ask what should happen.
- **Load-bearing assumptions:** name the assumption the favoured direction rests on, and ask
  what would have to be true for it to fail. Challenge it once; if the user holds it with the
  risk in view, log it as decided.

## Step 3 — Lay out the approaches

Generate several privately and drop the weak ones. Present 2-3 that differ on a real axis:
where state lives, who owns the invariant, sync versus async, build versus compose. A useful
spread is the minimal version (smallest change that meets the goal), the long-term version, and
one lateral reframing. Drop any approach that would appear in a generic article on the topic
without reference to this system. For each give: the mechanism in two sentences, what it is
best at, what it costs, and the bet it makes. Then recommend one, tied to the stated test for
"good", with anything larger than the goal needs offered as an option rather than the default.

## Step 4 — Run the log and converge

Update the log in the conversation whenever something settles, not at the end. Before closing,
combine what has been decided: two decisions that are each fine can produce an effect neither
answer considered ("events are fire-and-forget" plus "billing reads from events" means a lost
event is lost revenue). Ask about each such combination once. If several rounds pass and the
user's answers are still not predictable, say so and step back to the frame instead of grinding.

## Hand-offs

| need | use |
|---|---|
| capacity, cost, uptime numbers, or reviewing a finished design | system-design |
| what to build and what goes into a first version | product-scoping |
| whether to adopt, build or migrate to a specific technology | adopt-or-build |
| an agent system's topology, tool surface and stop conditions | agent-architecture |
| a strategic or career-level bet behind the design | liu-ayi |

## Output

During the discussion, show the log whenever it changes. At the end, write the design doc so
a capable builder could plan from it without returning to the conversation; optionally give it
to a fresh reader and ask only the questions that reader could not settle alone.

```
DECISION LOG
  Decided:  D1 <decision> — chosen over <alternative>: <reason> (user-chosen | user-approved)
  Open:     O1 <question> — would change <which part of the design>
  Rejected: R1 <option> — <reason>

DESIGN DOC — <topic>
Goal:            <one sentence; who benefits>
Good means:      <observable test(s)>
Constraints:     <binding ones only>
Non-goals:       <list>
Terms:           <term = precise meaning>   (only those sharpened in Step 2)
Approach:        <chosen mechanism, and why it beats the alternatives on the test above>
Decisions:       D1..Dn with rejected alternatives; flag as ADR-worthy only those that are hard
                 to reverse, surprising without context, and the result of a real trade-off
Assumptions:     <unverified, each with how to check it>
Open questions:  <only those that would change the design>
Left to builder: <deliberately undecided details>
```
