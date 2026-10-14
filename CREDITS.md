# Credits

Skills here were written from the sources below: read and rewritten, not copied.
Sources under CC BY-SA or CC BY-NC-SA contributed ideas only, no wording.

## Per-skill sources

- upstream/humanlayer-12-factor-agents/content/factor-02, factor-05, factor-07, factor-09 (prose CC BY-SA 4.0 — ideas only, no wording) — used in: agent-architecture
- upstream/muratcankoylan-agent-skills-for-context-engineering/skills/{multi-agent-patterns,tool-design,context-optimization,context-compression,self-managed-context,filesystem-context,long-horizon-prompting,harness-engineering,evaluation} (MIT) — used in: agent-architecture
- upstream/everything-claude-code/skills/{agent-architecture-audit,prompt-caching-strategy,regex-vs-llm-structured-text,cost-aware-llm-pipeline} (MIT) — used in: agent-architecture
- upstream/vila-lab/docs/architecture.md (CC BY-NC-SA 4.0 — ideas only, no wording) — used in: agent-architecture
- upstream/everything-claude-code/skills/{eval-harness,agent-eval,gan-style-harness} (MIT) — used in: agent-evals
- upstream/muratcankoylan-agent-skills-for-context-engineering/skills/{self-improvement-loops,harness-engineering,evaluation,advanced-evaluation} (MIT) — incl. judge position bias — used in: agent-evals
- upstream/anthropics-skills/skills/skill-creator, skills/mcp-builder/reference/evaluation.md (Apache-2.0) — used in: agent-evals
- upstream/gstack/eval-plan (MIT) — used in: agent-evals
- upstream/compound-engineering-plugin/.agents/skills/ce-skill-work/references/evaluate.md (MIT) — used in: agent-evals
- upstream/anthropics-skills/skills/claude-api/shared/evals/{eval-audit,build-eval,eval-hillclimb}.md — grade the end state, start from real failures, report spread, held-out split — used in: agent-evals
- upstream/compound-engineering-plugin/docs (MIT) — blinded arms, small-n paired evals — used in: agent-evals
- upstream/superpowers/skills/{subagent-driven-development,dispatching-parallel-agents} (MIT) — used in: agent-orchestration
- upstream/oh-my-claudecode/skills/team (MIT) — used in: agent-orchestration
- upstream/compound-engineering-plugin/skills/ce-work/references/execution-strategy.md (MIT) — exclusive file ownership, orchestrator-only git, bounded batch concurrency — used in: agent-orchestration
- upstream/anthropics-skills/skills/claude-api/shared/managed-agents-multiagent.md — when delegation fits — used in: agent-orchestration
- upstream/seanellyjames-deep-research-skill/SKILL.md (MIT) — concurrency cap and no nested spawning — used in: agent-orchestration
- upstream/everything-claude-code/skills/{agent-security-hardening,mcp-dependency-review,prompt-caching-strategy,llm-trading-agent-security,agent-architecture-audit} (MIT) — used in: agent-security
- upstream/vila-lab/README.md, docs/architecture.md (CC BY-NC-SA 4.0 — ideas only, no wording) — used in: agent-security
- upstream/muratcankoylan-agent-skills-for-context-engineering/skills/{self-managed-context,harness-engineering,self-improvement-loops} (MIT) — used in: agent-security
- Gambit Security, "AI Agents Are Hacking Online Retailers for $25 a Company" (2026), https://gambit.security/blog-posts/autonomous-ai-agents-online-retailers-25-a-company — used in: agent-security
- user-authored — used in: career-navigator
- upstream/gstack/cso (MIT) — boundary and invariant census first, sibling propagation, exploitability gating, three separate judgements, independent re-derivation, webhook review order, two-user and two-tenant negative controls — used in: app-security
- upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/security-reviewer.md (MIT) — confidence tied to attack-path traceability with a critical-impact override; feature-gate leaks — used in: app-security
- upstream/trailofbits-skills/plugins/{fp-check,differential-review} (CC BY-SA 4.0 — ideas only, no wording) — restate the claim before verifying, trace the validation chain, risk not size, git blame on removed security code, counted blast radius, exploit chains across rejected findings — used in: app-security
- upstream/getsentry-skills/skills/security-review (Apache-2.0) — attacker-controlled vs server-controlled input; do-not-flag list — used in: app-security
- third-party skill by Cocoon AI, kept verbatim (MIT; see LICENSE in this folder) — used in: architecture-diagram
- upstream/compound-engineering-plugin/skills/ce-code-review/references/{personas/*,action-class-rubric.md,subagent-template.md} (MIT) — correctness, security, performance and reliability lenses; P0–P3; check callers, guards and framework defaults — used in: code-review
- upstream/compound-engineering-plugin/skills/ce-simplify-code/references/personas/efficiency-reviewer.md (MIT) — unbounded structures, listener leaks — used in: code-review
- upstream/gstack/review (MIT) — sideways sweep, gate-integrity inventory, quote-or-cap confidence — used in: code-review
- upstream/mattpocock-skills/skills/engineering/code-review (MIT) — spec and standards as separate axes, smell vocabulary as fallback, repo conventions override — used in: code-review
- upstream/superpowers/skills/systematic-debugging (MIT) — root cause first, read the full error, one change at the source, three failed fixes means stop — used in: debugging
- upstream/compound-engineering-plugin/skills/ce-debug/references/{investigate,fix}.md (MIT) — observation-cited hypotheses, explicit invalidation — used in: debugging
- upstream/mattpocock-skills/skills/engineering/diagnosing-bugs (MIT) — reproduction loop as the first deliverable — used in: debugging
- upstream/gstack/investigate (MIT) — failure-shape routing; rerun, timeout and skip are not hypotheses — used in: debugging
- upstream/compound-engineering-plugin/skills/ce-debug (MIT) — convergent vs divergent fixes — used in: debugging
- upstream/gstack/qa (MIT) — regression-test value bar — used in: debugging
- upstream/addyosmani-agent-skills/skills/debugging-and-error-recovery (MIT) — check the layer (UI, network, backend) — used in: debugging
- authored for this toolkit from a stated need (frontend-or-backend triage) — request/response boundary isolation steps — used in: debugging
- upstream/everything-claude-code/skills/{database-migrations,docker-patterns} (MIT) — expand-migrate-contract, CONCURRENTLY, batched backfills — used in: production-ops
- upstream/compound-engineering-plugin/skills/ce-code-review/references/personas/data-migration-reviewer.md (MIT) — broken dual-write transitions — used in: production-ops
- upstream/jeffallan-claude-skills/skills/microservices-architect (MIT) — idempotency keys, idempotent saga steps, explicit retry budgets — used in: production-ops
- upstream/gstack/{land-and-deploy,canary} (MIT) — risk-scaled verification, baseline deviation, merge-shape-aware revert — used in: production-ops
- upstream/jeffallan-claude-skills/skills/{sre-engineer,monitoring-expert} (MIT) — multi-window burn-rate alerts, trend-based capacity alerts — used in: production-ops
- upstream/addyosmani-agent-skills/skills/observability-and-instrumentation (MIT) — entry-point log field — used in: production-ops
- upstream/everything-claude-code/skills/{latency-critical-systems,springboot-patterns} (MIT) — split latency signals; forwarded-header spoofing — used in: production-ops
- upstream/jeffallan-claude-skills/skills/devops-engineer/references/incident-response.md (MIT) — evidence before state-destroying actions, routing by incident type and regulatory clock, re-check after remediation — used in: production-ops
- upstream/axiomhq-skills/skills/sre (MIT) — discover the data's real fields before querying — used in: production-ops
- upstream/jeffallan-claude-skills/skills/architecture-designer/references/nfr-checklist.md (MIT) — numeric non-functional requirements before design; RPO and RTO as separate targets — used in: system-design
- upstream/everything-claude-code/skills/redis-patterns (MIT) — cache stampede named with a concrete fix — used in: system-design
- upstream/jeffallan-claude-skills/skills/cloud-architect/references/multi-cloud.md (MIT) — lock-in tier per service type; multi-cloud only for a named exit scenario — used in: system-design
- upstream/gstack/{plan-eng-review,review} (MIT) — named review battery; two-real-callers rule for extraction — used in: system-design
- upstream/compound-engineering-plugin/skills/ce-doc-review (MIT) — adequate needs no change; name the downstream cost — used in: system-design
- upstream/mattpocock-skills/skills/engineering/{domain-modeling,triage,codebase-design} (MIT) — decision-record gate, prior-solution search, deletion and seam tests — used in: system-design
- upstream/optimnow-cloud-finops-skills (CC BY-SA 4.0 — ideas only, no wording) — find waste from billing data per resource type — used in: system-design
- authored for this toolkit from a stated need (capacity and unit-cost estimation) — the estimation worksheet and the hot-spot checklist — used in: system-design
- upstream/superpowers/skills/verification-before-completion (MIT) — fresh evidence before claims, partial evidence, what each claim needs — used in: verification
- authored for this toolkit from a stated need (results challenged as unverified) — state how and where; answer challenges with evidence — used in: verification
- upstream/addyosmani-agent-skills/skills/doubt-driven-development (MIT) — artifact-only adversarial review, bounded cycles, "doubt theater" — used in: verification
- upstream/gstack/ship (MIT) — freshness by content, not by commit count — used in: verification
- upstream/yennanliu-investskill/plugins/us-stock-analysis/skills/economics-analysis (MIT) — never use remembered readings; provenance header; memory means low confidence; conflicting sources shown, never averaged — used in: macro-regime
- upstream/anthropics-financial-services/plugins/partner-built/lseg/skills/macro-rates-monitor (Apache-2.0) — fixed dashboard; real rate = nominal − breakeven; 2s10s and 3M-10Y slopes; cycle, policy, real-rate and financial-conditions synthesis — used in: macro-regime
- upstream/tradermonty-claude-trading-skills/skills/macro-regime-detector (MIT) — fail closed on missing inputs; require a sustained signal before calling a regime change — used in: macro-regime
- upstream/tradermonty-claude-trading-skills/skills/scenario-analyzer (MIT) — first- and second-order transmission to sectors with a confidence per link; independent second pass — used in: macro-regime
- upstream/marketingskills/skills/{competitor-profiling,competitors} (MIT) — observed / inferred / implication, not observed is not absent, dated snapshots, switching evidence both ways — used in: market-scan
- upstream/geekjourneyx-github-demand-radar/references/{rice-jtbd-rubric.md,pr-scan-guide.md,negative-filters.md} (MIT) — job inference, workaround and rejected-PR signals, not-noise table, standalone-tool ease — used in: market-scan
- upstream/mvanhorn-last30days-skill (MIT) — recency-windowed signals and the nothing-solid floor (installed tool; see toolkit/external.yaml) — used in: market-scan
- upstream/wanshuiyin-auto-claude-code-research-in-sleep/skills/novelty-check (MIT) — name the prior work before killing an idea — used in: market-scan
- upstream/compound-engineering-plugin/skills/ce-pov (MIT) — project floor and external floor, grade vocabulary, skeptic stance, reversibility-tiered effort, freeze-before-panel, "either is viable" — used in: adopt-or-build
- upstream/gstack/plan-ceo-review (MIT) — four explicit scope modes chosen before review — used in: product-scoping
- upstream/phuryn-pm-skills/pm-product-discovery/skills/opportunity-solution-tree (MIT) — opportunities not features, three solutions per opportunity, opportunity score — used in: product-scoping
- upstream/phuryn-pm-skills/pm-execution/skills/create-prd (MIT) — value proposition with an explicit alternatives slot; findings enter the PRD only if they change a decision — used in: product-scoping
- upstream/phuryn-pm-skills/pm-execution/skills/strategy-red-team (MIT) — load-bearing claims, steelman then attack, "fails if", ranked cheapest tests, no manufactured doubt — used in: product-scoping
- upstream/seanellyjames-deep-research-skill/SKILL.md (MIT) — question-the-question phase, argument-chain test, subagent cap — used in: verified-research
- upstream/jalald-verified-research/skills/verified-research/ (MIT) — opened-only citations, origin counting, independent verifier, tiered budgets, one gap-filling round — used in: verified-research
- upstream/wanshuiyin-auto-claude-code-research-in-sleep/skills/citation-audit (MIT) — wrong-context citation check — used in: verified-research
- user-authored framework (v1, 2026-03), restructured — used in: liu-ayi
- ideas from Liu Zhongjing (order output vs consumption, customary law, institutional capital, legitimacy before policy), paraphrased and restated as testable checks; his political programme and determinism are deliberately excluded — used in: liu-ayi
- Hume, Burke and Hayek on evolved institutions; Tetlock on reference classes and calibration (public literature) — used in: liu-ayi

## Adopted external projects (installed from their own source; not included)

- impeccable (Apache-2.0) — https://github.com/pbakaus/impeccable
- last30days (MIT) — https://github.com/mvanhorn/last30days-skill
- claude-code-hooks (MIT) — https://github.com/karanb192/claude-code-hooks
