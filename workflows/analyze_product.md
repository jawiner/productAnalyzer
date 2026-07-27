# Workflow: Analyze Product

## Objective
Produce a comprehensive, implementation-ready product improvement blueprint for any web app or website. Input: a URL. Output: a 15-agent deep analysis + synthesis report saved to `.tmp/`.

## Prerequisites
- `ANTHROPIC_API_KEY` set in `.env`
- `FIRECRAWL_API_KEY` set in `.env` (already present)
- Dependencies installed: `pip install -r requirements.txt`

---

## How to Run

```bash
python tools/product_analyzer.py https://example.com
```

The report is saved to `.tmp/report_<domain>_<date>.md`. Open it in any markdown viewer.

---

## What It Does (4 Phases)

### Phase 1: Discovery (~2 min)
- Scrapes the homepage with Firecrawl (~1 credit)
- Runs 7 parallel web searches: reviews, pricing, competitors, Reddit complaints, app store reviews, changelog, alternatives (~7 credits)
- Assembles a shared research bundle sent to all agents

### Phase 2+3: Expert Analysis (~15–25 min)
Runs 15 specialist agents in parallel batches (5 at a time). Each agent receives the full research context and produces 800–1500 words of domain-specific analysis:

| # | Agent | Focus |
|---|-------|-------|
| 1 | Product Strategy | Vision, roadmap, market fit, competitive moat |
| 2 | UX/UI Design | Interface, onboarding, user journeys, design system |
| 3 | Habit Formation | Behavioral psychology, engagement loops, retention design |
| 4 | Content & Journaling | Content creation UX, prompting, export, search |
| 5 | Health & Wellness | Fitness tracking, health integrations, gamification |
| 6 | Security & Privacy | Auth, encryption, compliance, trust signals |
| 7 | Scalability & Architecture | Tech stack, API design, multi-platform |
| 8 | Performance | Core Web Vitals, bundle size, caching, CDN |
| 9 | DevOps | CI/CD, reliability, observability, deployments |
| 10 | Testing & QA | Bug patterns, coverage, stability, quality |
| 11 | AI Architecture | AI features, personalization, LLM opportunities |
| 12 | Data & Analytics | Metrics, funnels, experimentation, instrumentation |
| 13 | Growth | Acquisition, activation, viral loops, retention |
| 14 | Accessibility | WCAG, screen readers, inclusive design |
| 15 | Business & Monetization | Pricing, conversion, unit economics, revenue model |

### Phase 4: Synthesis (~5–10 min)
A synthesis agent reads all 15 analyses and produces the master blueprint with:
- Executive Summary
- Critical Issues (Fix Immediately)
- Strategic Priorities (Next 90 Days)
- UX/Design Transformation
- Growth & Retention Blueprint
- Technical Architecture Recommendations
- AI & Intelligence Roadmap
- Monetization & Business Model
- Security & Trust Roadmap
- Accessibility & Inclusion Plan
- Performance Optimization Roadmap
- Competitive Strategy
- 12-Month Product Roadmap
- Success Metrics Dashboard
- Implementation Playbook

---

## Report Structure

```
.tmp/report_<domain>_<date>.md
├── Part I: Synthesis Blueprint   ← Start here. The master deliverable.
└── Part II: Specialist Analyses  ← Deep dives for each domain.
```

---

## Cost Estimates

| Resource | Per Run |
|----------|---------|
| Firecrawl credits | ~8–10 credits |
| Claude input tokens | ~300K–500K (shared context × 15 agents) |
| Claude output tokens | ~50K–80K (analyses + synthesis) |
| Approximate cost | $2–5 at Opus 4.8 pricing |
| Total runtime | 20–35 minutes |

---

## Common Issues

| Problem | Fix |
|---------|-----|
| `ANTHROPIC_API_KEY not set` | Add your key to `.env`: `ANTHROPIC_API_KEY=sk-ant-...` |
| Homepage scrape returns empty | Site blocks scrapers. The agents still work from search results. |
| Agent fails with rate limit | Reduce `MAX_WORKERS` in `product_analyzer.py` from 5 to 3. |
| Report truncated | Increase `max_tokens` in `synthesize()`. Default is 8000. |
| Search returns no results | Firecrawl search quota may be exhausted. Check your Firecrawl dashboard. |

---

## Output Handling
- Report lives in `.tmp/` — regenerable, not committed to git
- To share: copy `.tmp/report_*.md` to Google Docs or paste into Notion
- To re-run with different parameters: adjust `MAX_RESEARCH_CHARS`, `max_tokens`, or agent instructions in `product_analyzer.py`

---

## Tuning

**To focus agents on a specific domain** (e.g., only UX + Growth):
- Comment out unwanted agents in the `AGENTS` list in `product_analyzer.py`
- The synthesis prompt adapts automatically to however many analyses it receives

**To increase depth**:
- Raise `MAX_RESEARCH_CHARS` for more Firecrawl content per search
- Raise `max_tokens` per agent in `run_agent()` (currently 4000)
- Add more search queries in `gather_research()`

**To reduce cost**:
- Switch to `claude-sonnet-4-6` in `product_analyzer.py` (about 3× cheaper)
- Reduce `max_tokens` per agent from 4000 to 2000
