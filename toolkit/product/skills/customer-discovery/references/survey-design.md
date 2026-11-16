# Survey design

Read when a survey is proposed or under review: a WTP survey from `pricing`, a B2C demand
count, NPS / CSAT, or any questionnaire whose numbers will inform a decision.

## 1. Is a survey the right tool?

| what you need to learn | use |
|---|---|
| why people act as they do, in their words | interviews (this skill, Step 2–3) |
| how common a behaviour or answer is across a population | a survey |
| whether people can use something | a usability test |
| what a room thinks right now | a live poll, reported as that room's view, not a sample |

A survey counts; it does not explain. Run interviews first so the answer options use the
customers' own words and cover the options you would otherwise miss.

## 2. Start from the decision

1. Write the decision the survey informs, then the research questions (what you want to
   learn). Every survey question maps to one research question; a question that maps to none
   is cut.
2. Choose respondents from the goal, not from who is easy to reach. Surveying only current
   active users leaves out the people who tried and left — a coverage gap to name in the report.

## 3. Write questions about facts and behaviour

- Ask what people did, in a stated window, not what they usually do: "How many times did you
  export a report in the last 7 days? 0 / 1–2 / 3–5 / 6 or more", not "How often do you
  export? Often / Sometimes / Rarely". (Same rule as Iron law 2.)
- Short and plain, in the words people use; no leading wording; no negations.
- Broad before specific: the category before the product, the product before a feature.
- Put the qualifier first ("During your last order, how easy was it to…").
- Numeric options start at 0, have no gaps or overlaps, and cover the largest answer.
- "None", "Other" and "Prefer not to answer" are separate options.
- Five-point labelled scales by default; keep an established scale (NPS 0–10) as validated.
  NPS and other attitude scales measure attitude, not behaviour.
- A stated price or purchase intention in a survey is opinion-tier evidence here and in
  `pricing`, however many people give it.

## 4. Pilot before the full send

Send it to a small group first and check three things: do they finish, do they read each
question as meant, and are they the people you intended. Change the survey on what the pilot
shows, then send.

## 5. Report sample and non-response honestly

Beside every result state: who was asked and how they were reached, how many were asked, how
many answered (the response rate), and the coverage gaps.

- **Non-response:** when only the delighted and the furious answer, the average describes
  neither. Call a few non-respondents and say what they said.
- **Low-quality answers:** straight-lining a grid, impossibly fast completions, empty text.
  Flag responses that fail several checks, exclude on criteria stated in advance, and report
  how many were excluded and why.
- **No one-number reports:** cut results by the segment attribute from Iron law 4 (plan,
  role, tenure, market) before concluding anything.

## Output

```
Decision: <one line>   Research questions: <list>
Respondents: <who, how reached> | coverage gaps: <who is missing>
Questions: <each → research question it serves>
Pilot: <n, what changed>
Result: <figure> | asked <n>, answered <n> (<x>%), excluded <n> (<why>) | non-response check: <what>
```
