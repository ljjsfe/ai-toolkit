# Dialogue techniques

Procedures behind Steps 1–4 of `SKILL.md`. Read the section the step points to.

## Grounding the frame

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
- **Probe "should want" answers.** When a goal arrives as a virtue word (scalable, clean,
  flexible, robust), ask what concrete situation it must handle; if it sounds like justifying to
  an imagined reviewer, ask what they would want with no one to justify it to.

## Sharpen the language

Vague terms hide undecided design. Whenever one is load-bearing, stop and pin it.

- **Overloaded nouns:** "you say *account* — the paying organisation or the person logging in?"
  Propose one precise term per concept and use it from then on.
- **Boundary scenarios:** invent a concrete edge case that forces a choice — a partial refund, a
  retried webhook, an agent that times out mid-tool-call — and ask what should happen.
- **Load-bearing assumptions:** name the assumption the favoured direction rests on, and ask
  what would have to be true for it to fail. Challenge it once; if the user holds it with the
  risk in view, log it as decided.

## Playback and convergence

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
