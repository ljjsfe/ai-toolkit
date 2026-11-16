# Willingness-to-pay scripts, simplified conjoint, sample sizes

Read when preparing a WTP conversation or survey, or when sizing one.

## Before any price question

- Talk to whoever controls the budget. In B2B that is the economic buyer, interviewed apart
  from the champion and procurement; in B2C confirm the user is the payer (a parent, one
  partner for a household).
- Open as research, not a sale: "We're deciding what to build and want to understand what
  this would be worth to you. There's no price list and nothing to buy today." Never promise
  the researched price later.
- Describe the concept in one value paragraph (who it is for, the problem, the outcome)
  before asking about price; a misunderstood concept gets priced as something else.
- Use at least three of the instruments below on each person and look for agreement. Write
  down the reason behind every number; the reasons, not the numbers, reveal the segments.

## The question scripts, in order

1. **Current spend** (behaviour, so strongest of the spoken ones): "What do you pay today to
   deal with this — tools, people, workarounds?" Then cost it: hours × loaded rate.
2. **Value in their units:** "You said this eats four hours a week. What is that worth to your
   team?" Opens their value logic and shows what they compare you with.
3. **Three-point price probe**, asked in this order:
   - "What would be an acceptable price — a good deal you'd pay without thinking?"
   - "What price would feel expensive — you'd hesitate, but might still pay if it delivers?"
   - "At what price is it out of the question, however good it is?"
   Acceptable is the floor (pricing there leaves money behind); the band from acceptable to
   expensive is where prices live; prohibitive is a ceiling that needs a different segment.
   A narrow acceptable-to-prohibitive band reads as commodity; a very wide one means
   differentiated value or a confused concept — the follow-up "why" decides which.
4. **Purchase probability at a stated price:** "From 1 to 5, where 5 is 'I would definitely
   buy', how likely are you to buy this at $X?" Rotate 2–3 price points across respondents and
   read the fall in the share of 5s (scoring rules in SKILL.md Step 1).
5. **Forced trade-offs** when everything is "very valuable":
   - rank the 6–8 capabilities by importance to the purchase;
   - spread 100 points across them; under about 5 points on average is filler or killer;
   - would-you-rather at one price: "A has integrations but no analytics at $79, B the
     reverse at $79 — which?";
   - build-your-own: base product and price plus priced add-ons; what they skip at any price
     is a killer candidate.

B2B extra: before the interview, estimate economic value from the next-best alternative plus
the monetised difference (hours × loaded cost, errors × cost per error, revenue × margin).
Stated WTP above that estimate means the model is missing a value driver; find it first.

## Simplified conjoint (run it yourself)

1. Pick 3–4 attributes plus price, 2–3 levels each (integrations 3 vs 20; analytics basic vs
   advanced; support email vs dedicated; price $29 / $79 / $149).
2. Write 8–12 choice tasks, each showing 2–3 profiles plus "none of these". Rotate levels so
   each appears about equally often across tasks.
3. The respondent picks one profile per task (or none). They never see the design.
4. Record one CSV row per profile shown and run `scripts/conjoint_count.py choices.csv`: win
   rate per level = chosen ÷ shown. A big spread between an attribute's levels means it drives
   choice (leader); a near-zero spread is filler; a level whose presence lowers the win rate
   is a killer signal.
5. Price sensitivity = how much share the same package loses between two price levels, and
   how often "none" wins at the higher price.

It ranks features and brackets a price band; a launch that depends on the exact number
needs a properly designed conjoint.

## Sample sizes

| | B2B | B2C |
|---|---|---|
| method | 30–45 min depth interviews with the buying unit | 10–15 interviews to learn the value language, then a survey |
| per segment | 15–25 interviews; stop when three in a row bring no new value logic | 150–300 survey respondents for the probe and 1–5 scale |
| conjoint | rarely enough respondents; use trade-offs | about 200+ completed responses before reading win rates |
| below the floor | under 10 interviews: directional | under 150 (or 200 for conjoint): ranking and the three-point probe only |
| typical distortion | procurement under-quotes on purpose | respondents over-quote to be agreeable |
| behavioural check | pilot or LOI at a named price | priced landing pages, deposits, live A/B price tests on offers that really exist (if challenged, honour the lowest price any cohort saw) |
