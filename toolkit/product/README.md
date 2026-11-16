# product

- `skills/` — the toolkit's own product skills (discovery, scoping, pricing, experiments,
  analysis design, adopt-or-build).
- `vendor/` — six go-to-market skills vendored unchanged from coreyhaines31/marketingskills
  (`product-marketing`, `launch`, `onboarding`, `signup`, `churn-prevention`, `referrals`),
  pinned in `../vendored.json`. The repo's pricing, ab-testing, competitors, customer-research and
  copywriting skills are not vendored: `pricing`, `experiment-readout`, `market-scan`,
  `customer-discovery` and `writing` own those jobs here. The copies name sibling skills that are
  not installed (emails, paywalls, cro, ab-testing, marketing-ideas, offers, influencer-marketing,
  ads, revops).

Personal preferences (`personal/product.md` or `personal.local.md` here) are merged into the
installed copies as `PERSONAL.md`. Never edit `vendor/`: refresh it with
`python3 scripts/vendor_sync.py --update coreyhaines31-marketingskills`.
