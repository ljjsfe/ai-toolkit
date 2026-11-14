---
name: design-discussion
description: >-
  Hold an open-ended design conversation before planning: one question + guess per turn, frame goal
  and constraints before proposing, 2–3 distinct mechanisms, and a live decision log. Trigger on
  "discuss the design", 讨论方案/聊设计; once settled use system-design, spec, or agent-architecture.
version: 1.3.0
sources:
  - upstream/superpowers/skills/brainstorming (MIT) — think wide privately, nothing built before approval [port "generate several privately" "nothing gets built during the discussion"]
  - upstream/superpowers/skills/brainstorming/{SKILL.md,builder-check-prompt.md} (MIT) — design played back in short chunks each ending with a what-is-missing question; builder check as a required subagent pass with a prompt and three-pile triage; sizing and splitting the work [port "end the chunk by asking what is wrong or missing" "dispatch a fresh subagent" "minor, my call" "say how big the work is" "several independent designs"]
  - upstream/superpowers/skills/brainstorming/SKILL.md (MIT, v7.0.2) — ask only when the answer changes what gets built, else state the call as a proposal; why first, open-ended, no example answers; process steps are your own calls (release notes report blind-graded filler questions falling from 41 to 23) [port "would change what gets built" "no example answers attached" "never ask about process"]
  - upstream/addyosmani-agent-skills/skills/interview-me (MIT) — one question with a guess attached, "want vs should want" probe, predict-the-next-three stop test, bare assent is not a yes [port "with your guess attached" "justifying to an imagined reviewer" "reaction to the next three questions" "covers only what you actually showed"]
  - upstream/addyosmani-agent-skills/skills/idea-refine (MIT) — directions must differ, not vary; name what each bets on; a not-doing list [port "differ in mechanism, not in parameters" "and the bet it makes" "what this deliberately will not do"]
  - upstream/mattpocock-skills/skills/engineering/domain-modeling (MIT) — sharpen overloaded terms, edge-case scenarios, check the code, ADR only when hard to reverse, surprising and a real trade-off [port "overloaded nouns" "boundary scenarios" "check the code and raise" "surprising without context"]
  - upstream/mattpocock-skills/skills/engineering/grill-with-docs (MIT) — record decisions and terms as they settle, not at the end [port "whenever something settles, not at the end"]
  - upstream/compound-engineering-plugin/skills/ce-brainstorm/references/{approaches,dialogue,interaction-rules,settled-decisions}.md (MIT) — present all approaches before recommending, anti-genericness test, look up rather than ask, integration check, no self-settling of decisions [port "show all of them before you recommend" "generic article on the topic" "look it up instead of asking" "combine what has been decided" "only the user settles a decision"]
  - upstream/compound-engineering-plugin/skills/ce-brainstorm/references/blindspot-pass.md (MIT) — a blindspot pass for users who cannot evaluate the options themselves [port "a decision map, not a lesson" "not when they are merely undecided" "settled by evidence is not a decision"]
  - upstream/gstack/office-hours (MIT) — premise challenge (right problem, cost of doing nothing, what already exists); minimal versus long-term versus lateral approaches [port "is this the right problem" "the minimal version"]
  - upstream/gstack/office-hours (MIT) — landscape search before proposing; premises the user must explicitly agree to [port "search generic category terms" "where the conventional approach is wrong" "agree or disagree with each"]
  - upstream/janestreet-agent-skills/socratic-tutor/SKILL.md (MIT, https://github.com/janestreet/agent_skills) — ambiguous-intent confirmation guard before starting a multi-turn loop; never project unstated constraints onto the user's answer [port "ask in one sentence before starting the loop" "never attribute to the user a constraint"]
---

# Design Discussion

A design conversation is worth having because each answer changes the next question. Treat it
as a dialogue that converges on decisions, not an interview that collects requirements. If it is
unclear whether the user wants a quick recommendation or a multi-turn design discussion, ask in one
sentence before starting the loop.

## Iron laws

1. **One question per message, with your guess attached (except the why).** Ask only a question whose answer
   would change what gets built and that neither the request nor the code answers; otherwise state
   your call and reason as a proposal the user can correct. Ask the single question that most
   changes the design, state what you expect the answer to be and why, then wait. A list of
   questions gets skimmed answers and locks in a framing before the first answer arrives.
   **Exception — the why.** If the user has not said why they want this, ask that first, as one
   open question in their terms with no example answers attached and no guess: offered options
   replace their intent with yours. The guess applies to factual and design questions after that.
   **Never ask about process** (writing things up, where files go, whether to look further, how
   to show something): those are your calls — do them and say so. Not process: the mode check
   before the loop, consent before sending anything off the machine, and the blindspot offer.
2. **No approaches before the frame.** Until the goal, the binding constraints and the test for
   "good" are stated (or recorded as assumptions), do not propose a solution. Before the first
   proposal, ask what the user already has in mind; your framing anchors theirs.
3. **Approaches differ in mechanism, not in parameters.** Two caches with different TTLs are
   one approach. Show all of them before you recommend one.
4. **Keep a decision log and honour it.** A decided item is not re-asked; it reopens only on
   new evidence, which you name. Only the user settles a decision — your own proposal that they
   did not engage with stays *open*, "sounds good" covers only what you actually showed, and you
   never attribute to the user a constraint or implication they did not state.
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
- **Learn the landscape before proposing.** Once the problem is clear, look up how this kind of
  thing is usually built and where it usually goes wrong (existing tools, open-source options,
  common failure write-ups). Search generic category terms, never the user's product name or
  unreleased idea, and ask before sending anything off the machine if the work may be
  confidential. Read the top two or three sources, then say what the usual approach is and
  whether anything learned in this conversation suggests where the conventional approach is wrong
  here. If nothing does, say so and build on it. Without a search tool, say the landscape comes
  from model knowledge only.
- **Get the premises agreed, explicitly.** Before Step 3, write the premises the design will rest
  on (right problem, cost of doing nothing, what already exists, anything the landscape showed) as
  a numbered list and ask the user to agree or disagree with each. Silence or "sounds good" to a
  longer message is not agreement (law 4). A rejected premise sends you back to the frame.
- **Unfamiliar territory.** If the user cannot weigh the options in some area (they say so, or
  two answers in a row are "no idea, you decide" on a point that needs domain judgement), offer a
  blindspot pass: a decision map, not a lesson, of 3–7 decisions and hazards with your defaults.
  It is not when they are merely undecided; then keep asking. Procedure:
  `references/blindspot-pass.md` — read when that signal appears.
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

## Step 4 — Play back, run the log and converge

**Play the design back in chunks as it forms.** As soon as one part is understood well enough to
describe (who it serves, how one piece behaves), describe that part in about 200–300 words, then
return to questions about the next part. Only what the user said goes in as theirs; anything you
filled in is marked as your proposal with its reason. End the chunk by asking what is wrong or
missing. Playback and questions alternate to the end; the last chunk covers what is left.


Update the log in the conversation whenever something settles, not at the end. Before closing,
combine what has been decided: two decisions that are each fine can produce an effect neither
answer considered ("events are fire-and-forget" plus "billing reads from events" means a lost
event is lost revenue). Ask about each such combination once. If several rounds pass and the
user's answers are still not predictable, say so and step back to the frame instead of grinding.

## Step 5 — Size and split

Once an approach is chosen, say how big the work is in plain words; the user can override it.

| size | design doc | builder check |
|---|---|---|
| small change | short: what was already covered, a line or two per heading | no |
| project | the full doc below | required |

If it grows mid-discussion, say so and step up a size. If it is really several independent
designs (they share no decision and could ship in any order), say so, agree an order with the
user, and run the discussion for one at a time; record the others as open in the log.

## Hand-offs

| need | use |
|---|---|
| capacity, cost, uptime numbers, or reviewing a finished design | system-design |
| pinning settled behaviour as capability specs, change deltas and tasks | spec |
| what to build and what goes into a first version | product-scoping |
| whether to adopt, build or migrate to a specific technology | adopt-or-build |
| an agent system's topology, tool surface and stop conditions | agent-architecture |
| a strategic or career-level bet behind the design | liu-ayi |
| building mastery of an unfamiliar domain or codebase | socratic-tutor |

## Output

During the discussion, show the log whenever it changes. At the end, write the design doc so
a capable builder could plan from it without returning to the conversation. For a project-sized
design, run the builder check before handing it over: dispatch a fresh subagent with no
conversation history on the saved doc, sort its questions into three piles (answered already ·
minor, my call · the user's) and bring only the user's pile back, in one message. Prompt and
triage rules: `references/builder-check.md` — read when the doc is written.

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
