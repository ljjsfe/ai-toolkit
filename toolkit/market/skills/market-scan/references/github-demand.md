# GitHub demand collection

Read when the demand scan includes GitHub repos (an incumbent's tracker, or the open-source
tools in the space). The Search API is the only call that returns reaction counts.

## Queries

Set the windows first (`SINCE` for issues, default 30 days; `PR_SINCE` for PRs, default 90
days, because PRs are rarer and slower):

```bash
SINCE=$(date -v-30d +%Y-%m-%d)          # Linux: date -d '30 days ago' +%Y-%m-%d
PR_SINCE=$(date -v-90d +%Y-%m-%d)       # Linux: date -d '90 days ago' +%Y-%m-%d
STALE_BEFORE=$(date -v-180d +%Y-%m-%d)  # Linux: date -d '180 days ago' +%Y-%m-%d
R=owner/repo
```

| signal | query (`gh api "search/issues?q=…"`) |
|---|---|
| open issues, newest pain | `repo:$R+is:issue+is:open+created:>=$SINCE+-label:invalid+-label:duplicate&sort=reactions&order=desc&per_page=100` |
| closed issues that still drew a crowd | `repo:$R+is:issue+is:closed+created:>=$SINCE&sort=reactions&order=desc&per_page=30`, keep those with 10+ reactions and check whether the close was a fix or a refusal |
| rejected PRs (strongest) | `repo:$R+is:pr+is:closed+is:unmerged+created:>=$PR_SINCE&sort=reactions&order=desc&per_page=30` |
| open PRs with attention | `repo:$R+is:pr+is:open+created:>=$PR_SINCE&sort=reactions&order=desc&per_page=30` |
| stale PRs (open, untouched 180+ days) | `repo:$R+is:pr+is:open+updated:<$STALE_BEFORE&sort=reactions&order=desc&per_page=20` |

Run each as `GH_PAGER= gh api "search/issues?q=<query>" > <name>.json`, then
`scripts/demand_filter.py <name>.json --kind issue|pr-open|pr-rejected|pr-stale`. Merge the
kept items across queries, de-duplicate by number, rank by reactions + comments, and read the
top 10 in full. The search API allows about 30 calls a minute when authenticated; on 403 or 429
wait a minute. Check `gh auth status` first; a scan that never authenticated is "did not run",
not "nothing found".

Zero candidates: drop the label filter, then widen the issue window to 90 days; if still empty, say the repo is
quiet in the window rather than reporting no demand.

A rejected PR's close comment is the evidence: "out of scope" or "not on the roadmap" confirms
the gap; "superseded by #123" or "merged elsewhere" means it is served.

## Noise filters

Hard filters are mechanical and live in `scripts/demand_filter.py` (labels such as question,
invalid, duplicate; support-question titles such as "how do I…", "failed to install…"; empty,
stack-trace-only or "+1"-only bodies; bot authors and maintenance PR titles). Each dropped item
is printed with its reason so a wrong drop can be seen. Wontfix / "works as intended" / "not
planned" issues are never dropped: the script keeps them tagged `[confirmed gap]`, and the
queries do not exclude the wontfix label.

Judgement filters, applied by reading what survives:

- **Bikeshedding:** lively debate about colour, naming, icons or wording. Test: if it shipped,
  could anyone do a piece of work they cannot do now? If not, drop.
- **Wish with no context:** "please support X", "would be nice to have Y", with no scenario,
  no description of how the missing feature blocks their work and no workaround. Drop; a
  single sentence describing the blocked workflow is enough to keep it.
- **Governance and naming disputes** (branch renames, terminology, codes of conduct): not
  product demand; drop.
- **Fixed and quiet:** closed with a merged PR and no complaint of recurrence in the week after.
  Drop.

Never drop for these (they look like noise and are signal): many reactions with no comment
(reach), a long pasted script (a workaround), a "not on the roadmap" close (confirmed gap), an
issue open for years (chronic pain), angry wording (intensity).
