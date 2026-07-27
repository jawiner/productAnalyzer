# Workflow: Scrape Website

## Objective
Extract content or structured data from one or more web pages using the Firecrawl MCP tools.

## Prerequisites
- Firecrawl MCP server registered: `claude mcp add --transport http firecrawl https://mcp.firecrawl.dev/YOUR_API_KEY/v2/mcp`
- Verify with: `claude mcp list`

---

## Tools Available (via MCP — no Python script needed)

| Tool | Use When |
|------|----------|
| `firecrawl_scrape` | You need the content of a single, known URL |
| `firecrawl_crawl` | You need content from an entire site or section |
| `firecrawl_map` | You need to discover all URLs on a site before deciding what to scrape |
| `firecrawl_extract` | You need specific structured fields (price, title, dates, etc.) from a page |
| `firecrawl_search` | You need to find relevant pages AND get their content in one step |

---

## Decision Logic

1. **Single page, full content** → `firecrawl_scrape`
2. **Multiple pages, same site** → `firecrawl_crawl` with `maxDepth` and `limit` set conservatively
3. **Don't know which pages to scrape** → `firecrawl_map` first, then scrape or crawl targeted URLs
4. **Need specific data fields** → `firecrawl_extract` with a schema describing the fields
5. **Need to find pages first** → `firecrawl_search` with a query

---

## Usage Notes

### firecrawl_scrape
```
url: the target URL
formats: ["markdown"]   # markdown is cleanest for LLM consumption
```

### firecrawl_crawl
```
url: starting URL
maxDepth: 2             # keep low to avoid runaway crawls
limit: 20               # max pages — always set this
includePaths: ["/blog"] # optional: restrict to a path prefix
excludePaths: ["/tag"]  # optional: skip noisy sections
```

### firecrawl_extract
```
urls: [list of URLs]
prompt: "Extract the product name, price, and availability"
# or use schema for strict typing
```

### firecrawl_map
```
url: root URL
# Returns a list of all discovered URLs — use to plan a targeted crawl
```

---

## Handling Errors

| Error | Action |
|-------|--------|
| Rate limit (429) | Wait 60s, retry. For bulk jobs, add delay between requests. |
| Blocked / 403 | The site has anti-scrape protection. Note it in this workflow. Do not retry aggressively. |
| Timeout | Reduce crawl depth/limit and retry. |
| Empty content | Page may be JavaScript-heavy. Try `firecrawl_scrape` with `waitFor: 2000` if available. |

---

## Output Handling

- **Intermediates**: Save raw markdown to `.tmp/scrape_<domain>_<date>.md`
- **Deliverables**: If the output is a final artifact, push to Google Sheets, Docs, or Slides
- **Post-processing**: If content needs transformation (dedup, parse, format), use `tools/process_scraped_data.py`

---

## Known Constraints
- Firecrawl free tier: 500 credits/month. One page scrape ≈ 1 credit; crawl charges per page crawled.
- Always set `limit` on crawl jobs to avoid unexpected credit drain.
- Some sites (LinkedIn, Cloudflare-heavy) reliably block scraping — don't waste credits retrying them.
