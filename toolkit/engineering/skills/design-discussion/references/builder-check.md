# Builder check

Read when a project-sized design doc is written and before you hand it to the user.

The doc is meant to let a capable builder plan without coming back to the conversation. The only
honest test of that is a reader who was not in the conversation. You were, so you cannot be that
reader: you fill gaps from memory without noticing.

## Run it

1. Tell the user while writing up that a fresh reader will check the doc first and that you may
   come back once with a few questions.
2. Save the doc to a file, then dispatch a fresh subagent (no conversation history) with the
   prompt below, filling in the two placeholders. Do not add your own summary of the design: the
   doc must stand alone.
3. Do not hand the doc over until the check is back.
4. With no subagent tool, read the doc yourself as that builder, section by section, and say in
   the hand-over that the check was done by you, not by a fresh reader.

## Prompt

```
You are an experienced <domain: backend engineer, data engineer, game designer ...>. You have
been given the design document at <path> and asked to write a build plan from it. You cannot
ask the author anything.

Read the document. List only the questions you would still need answered to plan well: places
where you would have to guess and a wrong guess would change the plan. For each, give the
question and what in the plan depends on it. Rank by importance.

Leave out anything the document explicitly leaves to the builder, anything you could sensibly
decide yourself, and comments on wording. If nothing important is missing, reply
"nothing important left".
```

## Triage — three piles

Sort every question the builder returns:

| pile | test | what you do |
|---|---|---|
| answered already | the conversation, the decision log or the codebase settles it | write the answer into the doc; the gap was in the writing, not the design |
| minor, my call | a sensible builder could settle it without changing what gets built | decide it provisionally, mark it in the doc as your call, and list each one back to the user as open until they accept it |
| the user's | only the user can answer it, and the answer changes what gets built | collect for one message |

- Send the user's pile in **one** message, most important first, each with your guess attached;
  append your provisional calls from the minor pile so the user can accept or overturn them.
  This is the only round of questions the check produces; do not start a new interview.
- Update the doc with the answers and the decision log with any new decisions.
- Hand over the doc with a short list of the calls you made yourself, so the user can check those
  while reading.
- If the builder's top questions are all "the user's", the discussion stopped too early: say so
  and reopen the frame for those points rather than patching them in.
