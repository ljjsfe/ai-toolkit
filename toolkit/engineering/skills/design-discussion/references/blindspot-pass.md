# Blindspot pass

Read when the user cannot weigh the options in some part of the design (unfamiliar domain,
subsystem they have never touched) and questions are getting guesses instead of answers.

A question only extracts a requirement from someone who can judge the answer. On ground the user
does not know, turn their unknown unknowns into a short map of decisions they can now choose
between. It is a decision map, not a lesson: every item ends in something the user will decide,
delegate to you, or defer.

## When to offer it

- **Opening signal:** the user says they do not know the area ("never touched billing", "no idea
  what is possible here", "not sure what I should be asking").
- **Mid-discussion signal:** two answers in a row show they cannot evaluate the question at all
  ("no idea", "whatever you think") on a point that needs domain judgement.
- **Not when they are merely undecided.** Someone who understands the options but has not chosen
  needs the normal one-question loop. If you cannot tell which it is, keep asking.
- The offer covers only the flagged territory. The user stays the authority on their own goal,
  users, evidence and priorities; keep asking about those normally.

## The offer

Ask once per territory, as its own question, before the first substantive question into it:
"Part of this is in <territory>, which you said is unfamiliar. I can first lay out the decisions
you will face there, the realistic options and what I would default to, so you are choosing
rather than guessing. Or we carry on and I record my defaults as assumptions. Which do you
prefer?" Never slide into teaching unasked. If declined, do not offer again for that territory;
record your defaults as assumptions in the decision log. With no user to ask (a headless run),
treat it as declined.

## Building the map

Ground it before writing it:

- **Repo territory:** read the relevant code first; do not map it from memory.
- **External domain:** search current sources if a search tool exists; otherwise label each item
  "unverified, from model knowledge".
- **Settled by evidence is not a decision.** If the code or sources already answer an item, show
  the question with the found answer and its source as settled ground; do not put it to a vote,
  and do not resolve it silently either.
- **Hunt hazards:** things that fail silently (wrong defaults, filters that pass bad rows,
  escaping that corrupts output), conventions the code enforces that no doc states, and earlier
  half-built or reverted attempts at the same job; why they died is usually the trap.

Three to seven items, each at most four lines, ordered by how much the answer changes the shape
of the design (architecture-changing first, reversible choices and hazards last). Do not pad.

- **Decision item:** what it is in the user's words (define any unavoidable term and say what
  knowing it lets them decide) · why it matters for this design, tied to something they said ·
  2–4 options you would defend, one clause each on the trade-off that matters here · your default.
- **Hazard item:** what it is and what it changes about the task. No options and no default; if
  it forces a choice between real mitigations, that choice is its own decision item.

## Back into the discussion

Ask one question: "Which of these do you want to go through now? The rest take my default,
recorded as assumptions." Walk the chosen ones one per turn; a short menu of the mapped options is
fine here, because they were just explained. Log every unselected item as an assumption with its
default. The pass runs once per territory and never settles a decision on the user's behalf.
