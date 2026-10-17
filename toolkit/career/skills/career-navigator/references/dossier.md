# Dossier — the user's private campaign file

Advice without the user's real board is generic. The dossier holds that board across sessions.

**Location:** `~/.career/dossier.md`, on the user's machine only — never inside a git repository,
never sent to any service. It names real colleagues; treat it as confidential.

## How to use it

- **Every session:** if the file exists, read it before answering. If it doesn't and the user
  wants ongoing help, offer to create it from the template below by interviewing them (one
  section at a time, no more than five questions per turn).
- **After any session that changed something** (a new fact about a person, a card played, a
  stage move), propose the exact edits and write them only after the user agrees.
- **"下一步" / "what next" / "review my situation":** run the review below.

## Review — what to do next

1. What changed since the last entry? (people, reorg, results, conversations)
2. Update the power map and the trajectory of each key person.
3. Which stage is the user on (`roadmap.md`), and are its exit criteria met?
4. Re-take the leverage inventory (`tough-conversations.md`).
5. Choose the next move: one move, with the person, the script and the date. If the move is a
   conversation that asks for something, offer a rehearsal first (`rehearsal.md`).

## After-action review (after any real conversation or card played)

- What did I want? What did I get?
- What did they say that I didn't expect — and what does it tell me about their interests?
- Which line worked, which hurt?
- What is my next move, and when?

Record the answers in the cards-played table and the people table.

## Template

```markdown
# Career dossier — last updated YYYY-MM-DD

## Me
- Role / level / target level / target date:
- Stage (roadmap): 1 / 2 / 3 / 4 — why:
- Three adjectives (perception plan), started:
- Leverage inventory: outside option · replaceability · sponsor · timing · record

## People
| name | role | power now (1-5) | trajectory (rising/flat/falling) | wants | style | relation to me | last contact |
|---|---|---|---|---|---|---|---|

## Power map
- Who decides my rating / promotion:
- Who influences them:
- Factions and what they compete for:
- Recent changes (reorg, new leader, strategy):

## Sponsors and allies
| name | seat? | knows my work? | clout? | what I've done for them | what they've done for me | next touchpoint |
|---|---|---|---|---|---|---|

## Cards played
| date | with whom | card / ask | outcome | lesson |
|---|---|---|---|---|

## Open moves
- [ ] move — person — date
```
