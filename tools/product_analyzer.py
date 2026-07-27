#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Product Analyzer -- Multi-Agent AI System for Deep Product Research
Usage: python tools/product_analyzer.py <url>
Output: .tmp/report_<domain>_<date>.md
"""

import sys
import re
import time
from datetime import datetime
from urllib.parse import urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

import anthropic

# Add parent dir to path so we can import utils and firecrawl_client
sys.path.insert(0, str(Path(__file__).parent))
from utils import get_env, tmp_path
import firecrawl_client as fc


# --- Configuration -----------------------------------------------------------

MODEL = "claude-opus-4-8"
MAX_RESEARCH_CHARS = 3000   # per Firecrawl result, before sending to agents
MAX_WORKERS = 5              # parallel agent threads (stay under Claude rate limits)

Progress = Optional[Callable[[str, str], None]]  # (event, detail) -> None


# --- Agent Definitions -------------------------------------------------------

AGENTS = [
    {
        "id": "product_strategy",
        "name": "Product Strategy Agent",
        "expertise": "product vision, strategy, roadmap, competitive positioning, and market fit",
        "instructions": """Analyze the product from a product strategy perspective. Your analysis must cover:
- Current product vision and whether it's clearly communicated
- Target market definition and segmentation gaps
- Jobs-to-be-done the product does and doesn't address
- Feature prioritization framework -- what to build next and why
- Competitive moat and differentiation strategy
- Product-market fit signals (or lack thereof)
- Roadmap recommendations with clear rationale: what to cut, what to accelerate, what to add
- Strategic risks and how to mitigate them
Be specific and implementation-ready. Reference exact product details from the research.""",
    },
    {
        "id": "ux_design",
        "name": "UX/UI Design Agent",
        "expertise": "user experience, interface design, information architecture, and design systems",
        "instructions": """Analyze the product's UX/UI with the critical eye of a senior designer from Apple or Airbnb. Cover:
- First impressions and visual hierarchy assessment
- Onboarding flow analysis -- time-to-value, friction points, drop-off risks
- Information architecture and navigation clarity
- Core user journey mapping -- identify each step and rate its quality
- Design consistency and system quality
- Micro-interactions and emotional design opportunities
- Mobile vs desktop experience parity
- Specific UI components that need redesign (with concrete recommendations)
- Accessibility considerations in the design layer
- 10 specific, actionable design improvements with implementation guidance""",
    },
    {
        "id": "habit_formation",
        "name": "Habit Formation & Behavioral Psychology Agent",
        "expertise": "habit loops, behavioral psychology, engagement mechanics, and retention design",
        "instructions": """Analyze the product through the lens of habit formation and behavioral science. Cover:
- Habit loop analysis: cue -> routine -> reward for each core feature
- Variable reward schedules and their current effectiveness
- Streak mechanics, commitment devices, and their implementation quality
- Social proof and social accountability features
- Loss aversion and endowed progress mechanics
- Notification strategy: timing, content, personalization
- Friction audit -- where friction hurts retention vs. where intentional friction builds investment
- Fogg Behavior Model assessment (motivation + ability + prompt)
- Specific behavioral design patterns to add or improve
- Retention curve prediction based on current engagement design""",
    },
    {
        "id": "journaling_content",
        "name": "Content & Journaling Experience Agent",
        "expertise": "content creation UX, prompting systems, reflection mechanics, and writing experiences",
        "instructions": """Analyze the content creation and expression features of this product. Cover:
- Quality and variety of content creation prompts (if applicable)
- Writing/expression interface and its psychological safety
- Content discovery and browsing experience
- Search quality and findability of past content
- Templates, scaffolding, and guided creation flows
- Rich media support (images, voice, attachments)
- Export and portability of user-generated content
- Sentiment and mood tracking integration
- AI-assisted creation features (quality, relevance, tone)
- Privacy controls around personal content
- Recommendations to make content creation more meaningful and habit-forming""",
    },
    {
        "id": "fitness_wellness",
        "name": "Health & Wellness Integration Agent",
        "expertise": "fitness tracking, wellness features, health data integration, and motivation systems",
        "instructions": """Analyze the health, fitness, and wellness dimensions of this product. Cover:
- Goal setting and progress tracking effectiveness
- Health data integrations (Apple Health, Google Fit, wearables)
- Personalization of wellness recommendations
- Gamification of health metrics -- what works and what feels hollow
- Community and accountability features for health goals
- Scientific backing for any health claims or recommendations
- Streak and milestone celebration design
- Coach/mentor dynamics if present
- Physical activity and mental wellness balance
- Gaps in health feature coverage vs. competitor wellness apps
- Specific features to add to become a true wellness platform""",
    },
    {
        "id": "security",
        "name": "Security & Privacy Agent",
        "expertise": "application security, data privacy, compliance, and trust architecture",
        "instructions": """Audit the product's security and privacy posture. Cover:
- Authentication mechanisms and their strength (MFA, SSO, OAuth providers)
- Data encryption at rest and in transit signals
- Privacy policy clarity and data minimization principles
- GDPR/CCPA compliance indicators
- Data retention and deletion capabilities visible to users
- Third-party integrations and their data-sharing implications
- Security trust signals visible to users (certifications, audits)
- Potential attack surface concerns (from a product design perspective)
- Incident response and breach notification processes (visible to users)
- Recommendations to build user trust through privacy-by-design
- Competitive benchmarking on security/privacy vs. category leaders""",
    },
    {
        "id": "scalability_architecture",
        "name": "Scalability & Architecture Agent",
        "expertise": "system architecture, scalability patterns, technical debt, and platform design",
        "instructions": """Analyze the technical architecture from observable signals and best practices. Cover:
- Inferred tech stack and architectural patterns from public signals (job listings, APIs, performance)
- Scalability bottlenecks likely at current and 10x growth
- API design quality (if public API exists)
- Real-time features and their implementation quality
- Offline support and data synchronization strategy
- Multi-platform consistency (web, iOS, Android)
- Third-party dependencies and vendor lock-in risks
- Database and data architecture considerations for the use case
- Content delivery and global performance strategy
- Microservices vs. monolith trade-offs for this product stage
- Architecture recommendations for the next 18 months of growth""",
    },
    {
        "id": "performance",
        "name": "Performance Engineering Agent",
        "expertise": "web performance, Core Web Vitals, load time optimization, and runtime performance",
        "instructions": """Analyze the product's performance characteristics and optimization opportunities. Cover:
- Core Web Vitals assessment based on observable signals
- Time to First Contentful Paint and Largest Contentful Paint estimates
- JavaScript bundle size and code splitting strategy
- Image optimization and modern format adoption (WebP, AVIF)
- Caching strategy: browser, CDN, application-level
- Third-party script impact on performance
- Mobile performance vs. desktop parity
- Progressive Web App capabilities
- Performance budgets and monitoring strategy
- API response time characteristics from UX signals
- Top 10 performance optimizations ranked by impact and implementation effort""",
    },
    {
        "id": "devops",
        "name": "DevOps & Infrastructure Agent",
        "expertise": "CI/CD, deployment strategy, infrastructure reliability, and operational excellence",
        "instructions": """Analyze the DevOps maturity and infrastructure strategy from available signals. Cover:
- Deployment frequency and release strategy signals
- Downtime patterns and reliability SLA (from status pages, reviews, changelogs)
- Feature flag and gradual rollout capabilities
- Observability stack: logging, metrics, alerting, tracing
- Disaster recovery and backup strategy (user-visible signals)
- Environment parity (staging vs. production)
- Infrastructure cost optimization opportunities
- Container orchestration and cloud-native patterns
- On-call culture and incident management quality
- Recommendations for DevOps maturity improvement at this company stage""",
    },
    {
        "id": "testing_qa",
        "name": "Testing & Quality Assurance Agent",
        "expertise": "testing strategy, quality engineering, bug patterns, and QA processes",
        "instructions": """Analyze the product quality and testing posture from observable signals. Cover:
- Bug patterns and quality issues visible in reviews and changelogs
- Regression patterns and areas of recurring instability
- Test coverage inference from engineering culture signals
- Crash rate and stability signals from app store reviews
- Edge case handling quality (empty states, error messages, loading states)
- Cross-browser and cross-device compatibility signals
- Accessibility testing evidence
- Beta/early access programs and user feedback loops
- QA process maturity indicators
- Top quality risks that need immediate attention
- Recommendations for a world-class QA program at this product's stage""",
    },
    {
        "id": "ai_architecture",
        "name": "AI & Machine Learning Architecture Agent",
        "expertise": "AI feature design, ML systems, personalization, and intelligent product development",
        "instructions": """Analyze the AI/ML capabilities and opportunities for this product. Cover:
- Current AI features and their quality/effectiveness
- Personalization engine depth: what's being personalized and how well
- Recommendation systems and their relevance quality
- Natural language interfaces and their capabilities
- AI-generated content quality and appropriateness
- Training data sources and potential biases
- Model update frequency and improvement signals
- AI transparency and explainability to users
- Opportunities to add AI that would create step-change improvement
- LLM integration opportunities (agents, copilots, smart suggestions)
- Build vs. buy vs. fine-tune decision framework for this product's AI roadmap""",
    },
    {
        "id": "data_analytics",
        "name": "Data & Analytics Agent",
        "expertise": "product analytics, data strategy, metrics frameworks, and instrumentation",
        "instructions": """Analyze the product's data strategy and analytics maturity. Cover:
- North Star Metric identification and its quality
- Supporting metrics framework (input metrics, guardrail metrics)
- Funnel analysis: where users likely drop off based on UX signals
- Cohort retention analysis strategy recommendations
- A/B testing capabilities and experimentation culture signals
- User segmentation depth and personalization data utilization
- Data literacy in product decisions (signals from changelog, blog)
- Privacy-preserving analytics approaches
- Real-time vs. batch analytics trade-offs for this product
- Analytics toolstack recommendations
- Dashboard and reporting strategy for the product team""",
    },
    {
        "id": "growth",
        "name": "Growth & User Acquisition Agent",
        "expertise": "growth engineering, viral loops, acquisition channels, and activation optimization",
        "instructions": """Analyze the product's growth strategy and improvement opportunities. Cover:
- Current acquisition channels (organic, paid, viral, partnership signals)
- Viral coefficient and sharing mechanics quality
- Referral program design and effectiveness
- Activation rate optimization opportunities -- the critical first 5 minutes
- Onboarding completion funnel assessment
- Content marketing and SEO strategy signals
- App store optimization quality (screenshots, description, ratings strategy)
- Paywall placement and conversion optimization
- Retention loop design: what brings users back daily/weekly
- Network effects: does the product get better with more users?
- Growth model: which levers matter most and why
- 90-day growth experiment roadmap with hypotheses and success metrics""",
    },
    {
        "id": "accessibility",
        "name": "Accessibility Agent",
        "expertise": "WCAG compliance, inclusive design, assistive technology support, and universal access",
        "instructions": """Audit the product's accessibility and inclusive design maturity. Cover:
- WCAG 2.1 AA compliance assessment from visible signals
- Screen reader compatibility signals
- Keyboard navigation completeness
- Color contrast ratios and visual accessibility
- Touch target sizes on mobile
- Dynamic text size support
- Animation and motion sensitivity controls
- Alternative text for images and media
- Form label and error message clarity
- Cognitive accessibility: simplicity, predictability, error prevention
- Internationalization and RTL language support
- 15 specific accessibility improvements with WCAG success criteria references
- Business case for accessibility investment at this product's scale""",
    },
    {
        "id": "business_monetization",
        "name": "Business & Monetization Agent",
        "expertise": "revenue models, pricing strategy, unit economics, and sustainable business design",
        "instructions": """Analyze the business model and monetization strategy. Cover:
- Current pricing model and tier structure assessment
- Free-to-paid conversion funnel design
- Pricing page clarity and value communication
- Annual vs. monthly billing incentive structure
- Enterprise/B2B opportunity signals
- Churn risk factors from product design
- LTV optimization opportunities
- Pricing psychology and anchoring effectiveness
- Competitor pricing benchmark
- Revenue diversification opportunities (marketplace, API, white-label)
- Unit economics assessment: CAC signals, LTV drivers
- Pricing experiments to run in the next 6 months
- Long-term business model evolution recommendations""",
    },
]


# --- Phase 1: Discovery -------------------------------------------------------

def gather_research(url: str, on_progress: Progress = None) -> dict:
    """Scrape the target and run parallel web searches. Returns a research bundle."""
    domain = urlparse(url).netloc.replace("www.", "")
    product_name = domain.split(".")[0].title()

    print(f"\n[Phase 1] Gathering research on {product_name} ({url})")
    if on_progress:
        on_progress("phase", "Phase 1: Discovery")
        on_progress("scraping", f"Scraping {url}...")

    try:
        homepage_md = fc.scrape(url)[:6000]
        if on_progress:
            on_progress("scrape_done", "Homepage scraped")
    except Exception as e:
        print(f"  Warning: homepage scrape failed: {e}")
        homepage_md = f"Homepage could not be scraped: {e}"
        if on_progress:
            on_progress("scrape_failed", f"Homepage scrape failed: {e}")

    queries = [
        f"{product_name} app review user feedback",
        f"{product_name} pricing plans features",
        f"{product_name} competitors alternatives comparison",
        f"{product_name} reddit complaints problems",
        f"{product_name} app store reviews rating",
        f"{product_name} changelog new features 2024 2025",
        f"best {domain.split('.')[0]} alternatives {product_name} comparison",
    ]

    search_results = {}
    print(f"  Running {len(queries)} parallel searches...")

    def run_search(q: str) -> tuple[str, str]:
        try:
            return q, fc.search_text(q, limit=4, max_chars_per_result=1500)
        except Exception as e:
            return q, f"Search failed: {e}"

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_search, q): q for q in queries}
        for future in as_completed(futures):
            q, result = future.result()
            search_results[q] = result
            print(f"  [done] {q[:60]}...")
            if on_progress:
                on_progress("search_done", q)

    return {
        "url": url,
        "domain": domain,
        "product_name": product_name,
        "homepage": homepage_md,
        "searches": search_results,
    }


def format_research_context(research: dict) -> str:
    """Format the research bundle into a single context string for agents."""
    parts = [
        f"# Product Research: {research['product_name']}",
        f"URL: {research['url']}",
        "",
        "## Homepage Content",
        research["homepage"],
        "",
        "## Web Research",
    ]
    for query, result in research["searches"].items():
        parts.append(f"\n### Search: {query}")
        parts.append(result)

    return "\n".join(parts)


# --- Phase 2+3: Expert Agent Analysis ----------------------------------------

def run_agent(agent: dict, research_context: str, product_name: str, client: anthropic.Anthropic, on_progress: Progress = None) -> dict:
    """Run a single specialist agent. Returns {id, name, output}."""

    system_prompt = f"""You are the {agent['name']}, an elite specialist with deep expertise in {agent['expertise']}.

You are part of a world-class product analysis team producing an implementation-ready blueprint for improving {product_name}. Your analysis should match the quality of work produced by top product teams at Apple, Google, Airbnb, Notion, Stripe, and Linear.

Universal standards for your analysis:
- Be specific -- reference actual product details from the research, not generic advice
- Be implementation-ready -- recommendations must be actionable by a product team next sprint
- Be quantified -- include metrics, timelines, and success criteria wherever possible
- Be critical -- identify real problems, not just opportunities. Name what's broken.
- Be comprehensive -- cover your entire domain. Nothing important should be missing.
- Structure with clear headers and sub-sections
- Use bullet points for scannable findings, paragraphs for strategic context
- Length: 800-1500 words. Quality over quantity."""

    user_message = f"""{research_context}

---

## Your Assignment

{agent['instructions']}

Produce your complete analysis now. Be specific, critical, and implementation-ready."""

    print(f"  >> Running {agent['name']}...")
    if on_progress:
        on_progress("agent_start", agent["name"])
    start = time.time()

    with client.messages.stream(
        model=MODEL,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        final = stream.get_final_message()

    output = ""
    for block in final.content:
        if block.type == "text":
            output = block.text
            break

    elapsed = time.time() - start
    print(f"  [done] {agent['name']} ({elapsed:.0f}s, {len(output)} chars)")
    if on_progress:
        on_progress("agent_done", agent["name"])

    return {"id": agent["id"], "name": agent["name"], "output": output}


def run_all_agents(research: dict, research_context: str, client: anthropic.Anthropic, on_progress: Progress = None) -> list[dict]:
    """Run all 15 agents in parallel batches. Returns sorted list of results."""
    product_name = research["product_name"]
    results = []

    print(f"\n[Phase 2+3] Running {len(AGENTS)} specialist agents in parallel batches...")
    if on_progress:
        on_progress("phase", f"Phase 2-3: Running {len(AGENTS)} specialist agents")

    batch_size = MAX_WORKERS
    for i in range(0, len(AGENTS), batch_size):
        batch = AGENTS[i : i + batch_size]

        with ThreadPoolExecutor(max_workers=batch_size) as pool:
            futures = {
                pool.submit(run_agent, agent, research_context, product_name, client, on_progress): agent
                for agent in batch
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    agent = futures[future]
                    print(f"  [FAIL] {agent['name']} failed: {e}")
                    if on_progress:
                        on_progress("agent_failed", f"{agent['name']}: {e}")
                    results.append({
                        "id": agent["id"],
                        "name": agent["name"],
                        "output": f"Analysis failed: {e}",
                    })

    id_order = {a["id"]: idx for idx, a in enumerate(AGENTS)}
    results.sort(key=lambda r: id_order.get(r["id"], 999))
    return results


# --- Phase 4: Synthesis -------------------------------------------------------

def synthesize(research: dict, agent_results: list[dict], client: anthropic.Anthropic, on_progress: Progress = None) -> str:
    """Synthesis agent combines all 15 analyses into the final blueprint."""
    product_name = research["product_name"]

    print(f"\n[Phase 4] Running synthesis agent...")
    if on_progress:
        on_progress("phase", "Phase 4: Synthesis")
        on_progress("synthesis_start", "Synthesizing all analyses into master blueprint...")

    analyses = "\n\n".join(
        f"## {r['name']}\n\n{r['output']}" for r in agent_results
    )

    system_prompt = f"""You are the Chief Product Officer synthesizing findings from a 15-person elite analysis team. Your task is to produce the definitive improvement blueprint for {product_name}.

This blueprint will be used directly by founders, PMs, and engineers. It must be:
- Actionable: every recommendation has an owner, timeline, and success metric
- Prioritized: not everything matters equally -- help the team focus
- Cross-functional: connect insights across design, engineering, growth, and business
- Honest: name what's broken, not just what could be better
- Implementation-ready: a team could start executing next Monday

Format using markdown with clear headers. This is the final deliverable."""

    user_message = f"""# Product: {product_name}
URL: {research['url']}

Below are 15 specialist analyses. Synthesize them into a comprehensive, implementation-ready product blueprint.

---

{analyses}

---

## Your Synthesis Task

Produce a complete Product Improvement Blueprint with these exact sections:

### Executive Summary
3-5 paragraphs. Current state assessment, biggest opportunities, and the single most important thing to fix first.

### Critical Issues (Fix Immediately)
The 5 most urgent problems that are hurting the product today. For each: the problem, the impact, and the fix.

### Strategic Priorities (Next 90 Days)
Top 10 initiatives ranked by impact. For each: what to build, why it matters, success metrics, effort estimate (S/M/L).

### UX/Design Transformation
Specific design improvements with wireframe-level specificity. What to change, why, and expected impact.

### Growth & Retention Blueprint
Full funnel optimization plan. Activation -> Engagement -> Retention -> Referral. Specific experiments to run.

### Technical Architecture Recommendations
What to build, refactor, or sunset in the technical stack. Prioritized by impact on user experience and scalability.

### AI & Intelligence Roadmap
Where to add AI, what to build vs. buy, and how to use AI for competitive differentiation.

### Monetization & Business Model
Pricing changes, new revenue streams, conversion optimization. With expected impact on revenue.

### Security & Trust Roadmap
Privacy improvements, security posture, and trust signals to add.

### Accessibility & Inclusion Plan
Specific WCAG improvements and timeline to reach AA compliance.

### Performance Optimization Roadmap
Top performance wins ranked by user impact. Include specific metrics to improve.

### Competitive Strategy
Where the product wins, where it loses, and how to build a sustainable competitive moat.

### 12-Month Product Roadmap
Quarter-by-quarter plan connecting all recommendations into a coherent sequence.

### Success Metrics Dashboard
The 10-15 metrics that define success for this product, with targets and measurement methods.

### Implementation Playbook
How to execute this blueprint: team structure, sprint cadence, decision rights, and how to measure progress.

Produce the complete blueprint now. Be specific, critical, and implementation-ready. This is world-class work."""

    with client.messages.stream(
        model=MODEL,
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        final = stream.get_final_message()

    output = ""
    for block in final.content:
        if block.type == "text":
            output = block.text
            break

    print(f"  [done] Synthesis complete ({len(output)} chars)")
    if on_progress:
        on_progress("synthesis_done", f"Blueprint complete ({len(output):,} chars)")
    return output


# --- Report Assembly ----------------------------------------------------------

def assemble_report(research: dict, agent_results: list[dict], synthesis: str) -> str:
    """Assemble the final markdown report."""
    product_name = research["product_name"]
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    header = f"""# {product_name} -- Product Analysis Blueprint
**Generated:** {date_str}
**URL:** {research['url']}
**Agents:** {len(agent_results)} specialists + synthesis

---

"""

    specialist_sections = "\n\n---\n\n".join(
        f"## {r['name']}\n\n{r['output']}" for r in agent_results
    )

    return (
        header
        + "# Part I: Synthesis Blueprint\n\n"
        + synthesis
        + "\n\n---\n\n# Part II: Specialist Analyses\n\n"
        + specialist_sections
    )


# --- Public API (used by Streamlit UI) ---------------------------------------

def run_analysis(url: str, on_progress: Progress = None) -> str:
    """Run the full 4-phase pipeline. Returns the assembled report as a string."""
    if not url.startswith("http"):
        url = "https://" + url

    # Create client once here -- never inside threads
    api_key = get_env("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    research = gather_research(url, on_progress=on_progress)
    research_context = format_research_context(research)

    if on_progress:
        on_progress("research_ready", f"Research context: {len(research_context):,} chars")

    agent_results = run_all_agents(research, research_context, client, on_progress=on_progress)
    synthesis = synthesize(research, agent_results, client, on_progress=on_progress)
    report = assemble_report(research, agent_results, synthesis)

    # Save to .tmp/
    domain_slug = re.sub(r"[^\w]", "_", research["domain"])
    date_slug = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"report_{domain_slug}_{date_slug}.md"
    output_path = tmp_path(filename)
    output_path.write_text(report, encoding="utf-8")

    if on_progress:
        on_progress("done", str(output_path))

    return report


# --- CLI Entry Point ----------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python tools/product_analyzer.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"\n{'='*60}")
    print(f"  Product Analyzer -- Multi-Agent System")
    print(f"{'='*60}")
    print(f"  Target: {url}")
    print(f"  Model: {MODEL}")
    print(f"  Agents: {len(AGENTS)} specialists")
    print(f"{'='*60}\n")

    start_total = time.time()
    report = run_analysis(url)
    elapsed = time.time() - start_total

    print(f"\n{'='*60}")
    print(f"  Analysis complete in {elapsed/60:.1f} minutes")
    print(f"  Size: {len(report):,} characters ({len(report.splitlines())} lines)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
