# Analysis design templates

Fill only what the question needs; a quick pull gets one line per field.

## Analysis brief

```markdown
# Brief: <title>   Date: <YYYY-MM-DD>   Requester: <who>   Audience: <who reads the result>

Context: <two sentences: what is happening, why now>

| rung | statement |
|---|---|
| goal | <business outcome> |
| decision | <action the answer changes; or "reporting only"> |
| metric | <name, spec below> |
| hypothesis | <expected finding and why> |

Success criterion: <falsifiable condition>
Kill criterion: <result that rejects the hypothesis>; smallest effect worth acting on: <x>
Dimensions: <dimension> — <what a difference would tell us> (one line each)
Period: <start..end>   Granularity: <day/week/month>   Comparison: <baseline and why it is fair>
Deliverable: <one-line answer / report / table / deck>
```

## Metric spec

```markdown
## Metric: <name>
Plain definition: <one sentence>
Formula: <exact calculation>
Unit of analysis: <one row = …>   Reported grain: <per user per week, …>
Numerator: <what is counted> — source <table.column>
Denominator: <what is counted> — source <table.column>   (or "none, absolute")
Filters / exclusions: <test, internal, bots, refunds, …>
Window: <anchoring and timezone>
Owner: <team>   Refresh / latency: <cadence, delay>
Known gotchas: <late data, definition changes, outages, partial periods>
Related: drivers <…>; alternatives <…>
Typical range: <band and its basis, if known — never guessed>
```

## Data-quality report

```markdown
Data: <source, slice, extraction query or file>
Probe: <command run> → rows <n>, columns <n>, period <min..max>

| severity | check | finding | rows affected | handling |
|---|---|---|---|---|
| BLOCKER / WARNING / INFO | <check> | <what> | <n> | <fix, exclusion or caveat; never silent> |

Call: proceed / proceed with caution / blocked — <reason>
```

## Tracking-gap table and instrumentation request

```markdown
| requirement | needed for | grain | period | status | source | notes |
|---|---|---|---|---|---|---|
| <event/field> | <plan part> | <per user/session/event> | <range> | available / partial / missing / derivable | <table.column> | <proxy and its confidence> |

### Instrumentation request: <event_name>
Trigger: <exactly when it fires>
Properties: <name> (<type>, required Y/N) — <meaning>; …
Priority: P0-Critical / P1-High / P2-Medium / P3-Low
Unblocks: <question or decision>
Depends on: <other instrumentation, or none>
```
