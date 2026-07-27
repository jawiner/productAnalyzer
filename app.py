"""
Product Analyzer -- Streamlit UI
Run with: python -m streamlit run app.py --browser.gatherUsageStats false
"""

import sys
sys.dont_write_bytecode = True

import io
import os
import contextlib
import traceback
import time
import threading
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load .env immediately with override=True so env vars are always current,
# regardless of module reload order or Streamlit's module caching.
_root = Path(__file__).parent
load_dotenv(_root / ".env", override=True)

import streamlit as st

# Force fresh import of our modules every time Streamlit reruns this script.
_tools_path = str(_root / "tools")
if _tools_path not in sys.path:
    sys.path.insert(0, _tools_path)

for _mod in ["utils", "firecrawl_client", "product_analyzer"]:
    sys.modules.pop(_mod, None)

from product_analyzer import run_analysis, AGENTS

AGENT_NAMES = [a["name"] for a in AGENTS]

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Product Analyzer",
    page_icon=":mag:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .stApp { max-width: 1100px; margin: 0 auto; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Session state
# "job" is a plain Python dict shared between main thread and worker thread.
# The worker thread ONLY mutates this dict -- never calls any st.* function.
# ---------------------------------------------------------------------------

if "job" not in st.session_state:
    st.session_state.job = None

# ---------------------------------------------------------------------------
# Header & input
# ---------------------------------------------------------------------------

st.title("Product Analyzer")
st.markdown("*15 specialist agents -- deep implementation-ready product blueprint*")
st.divider()

job = st.session_state.job
is_running = job is not None and job["running"]

col1, col2 = st.columns([4, 1])
with col1:
    url_input = st.text_input(
        "URL",
        placeholder="https://notion.so",
        label_visibility="collapsed",
        disabled=is_running,
    )
with col2:
    run_btn = st.button(
        "Analyze",
        type="primary",
        use_container_width=True,
        disabled=is_running or not url_input,
    )

st.caption(f"Runs {len(AGENTS)} specialist agents in parallel -- ~25-35 min -- Opus 4.8")

# ---------------------------------------------------------------------------
# Start analysis
# ---------------------------------------------------------------------------

if run_btn and url_input and not is_running:
    url = url_input if url_input.startswith("http") else "https://" + url_input

    # Plain dict -- worker thread mutates this directly (no st.* calls in thread)
    job = {
        "url": url,
        "running": True,
        "done": False,
        "report": None,
        "error": None,
        "log": [],
        "agents_done": [],
        "agents_active": [],
        "start": time.time(),
    }
    st.session_state.job = job

    def on_progress(event: str, detail: str) -> None:
        """Mutates `job` dict only. Never touches st.* -- called from worker thread."""
        if event == "phase":
            job["log"].append(f"--- {detail} ---")
        elif event == "scraping":
            job["log"].append("Scraping homepage...")
        elif event == "scrape_done":
            job["log"].append("Homepage scraped")
        elif event == "scrape_failed":
            job["log"].append(f"Homepage scrape skipped ({detail[:80]})")
        elif event == "search_done":
            q = detail[:65] + "..." if len(detail) > 65 else detail
            job["log"].append(f"Search: {q}")
        elif event == "research_ready":
            job["log"].append(detail)
        elif event == "agent_start":
            if detail not in job["agents_active"]:
                job["agents_active"].append(detail)
        elif event == "agent_done":
            if detail in job["agents_active"]:
                job["agents_active"].remove(detail)
            if detail not in job["agents_done"]:
                job["agents_done"].append(detail)
        elif event == "agent_failed":
            job["log"].append(f"Agent failed: {detail[:100]}")
        elif event == "synthesis_start":
            job["log"].append("Synthesizing all analyses...")
        elif event == "synthesis_done":
            job["log"].append(f"Synthesis complete: {detail}")
        elif event == "done":
            job["log"].append(f"Saved: {detail}")

    def worker() -> None:
        sink = io.StringIO()
        try:
            with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                report = run_analysis(url, on_progress=on_progress)
            job["report"] = report
        except BaseException as exc:
            job["error"] = traceback.format_exc()
        finally:
            job["running"] = False
            job["done"] = True

    threading.Thread(target=worker, daemon=True).start()
    st.rerun()

# ---------------------------------------------------------------------------
# Progress display (while running or after done)
# ---------------------------------------------------------------------------

job = st.session_state.job  # re-read after possible mutation above

if job is not None:
    elapsed = time.time() - job["start"]
    done_count = len(job["agents_done"])
    active_set = set(job["agents_active"])
    done_set = set(job["agents_done"])

    # Status header
    if job["running"]:
        st.markdown(f"### Running... {elapsed/60:.1f} min elapsed")
    elif job["error"]:
        st.error(f"Analysis failed: {job['error']}")
    else:
        st.success(f"Complete in {elapsed/60:.1f} minutes")

    # Log
    if job["log"]:
        with st.expander("Progress log", expanded=job["running"]):
            st.text("\n".join(job["log"][-40:]))

    # Agent grid
    st.markdown(f"**Agents: {done_count} / {len(AGENTS)} complete**")
    cols = st.columns(3)
    for i, name in enumerate(AGENT_NAMES):
        with cols[i % 3]:
            if name in done_set:
                st.markdown(f"**[done]** {name}")
            elif name in active_set:
                st.markdown(f"*[running]* {name}")
            else:
                st.markdown(f"[ ] {name}")

    # Auto-refresh while running
    if job["running"]:
        time.sleep(3)
        st.rerun()

# ---------------------------------------------------------------------------
# Report output
# ---------------------------------------------------------------------------

if job is not None and job["done"] and job["report"]:
    report = job["report"]
    analyzed_url = job["url"]
    domain = analyzed_url.replace("https://", "").replace("http://", "").split("/")[0]
    date_slug = datetime.now().strftime("%Y%m%d")
    filename = f"report_{domain}_{date_slug}.md"

    st.divider()
    st.download_button(
        label="Download Report (.md)",
        data=report.encode("utf-8"),
        file_name=filename,
        mime="text/markdown",
    )
    st.divider()
    st.markdown(report)
