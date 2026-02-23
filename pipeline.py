"""
pipeline.py - End-to-end data pipeline
Scrape → Classify → Store → Report
Run manually or schedule with APScheduler
"""

import asyncio
from datetime import datetime
from scraper import scrape_all_sources, SAMPLE_TOOLS
from classifier import hybrid_classify
from llm_engine import classify_and_enrich_tool, generate_trend_summary
from database import init_db, save_tool, clear_tools, log_run, get_all_tools, get_tool_count


def process_tools(raw_tools: list, use_llm: bool = True) -> list:
    """Classify and enrich each tool."""
    enriched = []

    for i, tool in enumerate(raw_tools):
        print(f"  [{i+1}/{len(raw_tools)}] Processing: {tool['name']}")

        llm_fn = classify_and_enrich_tool if use_llm else None

        result = hybrid_classify(
            name=tool["name"],
            description=tool["description"],
            llm_fn=llm_fn,
        )

        # Small delay to avoid Groq TPM rate limit (6000 tokens/min on free tier)
        if use_llm:
            import time
            time.sleep(0.8)

        result["name"] = tool["name"]
        result["description"] = tool["description"]
        result["source"] = tool.get("source", "Unknown")
        enriched.append(result)

    return enriched


def run_pipeline(use_sample_data: bool = False, use_llm: bool = True):
    """
    Full pipeline run:
    1. Scrape (or use sample data)
    2. Classify + enrich
    3. Save to DB
    4. Generate trend summary
    """
    print(f"\n{'='*50}")
    print(f"AI Tool TrendAnalyzer Pipeline")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}\n")

    init_db()

    # Step 1: Scrape
    if use_sample_data:
        print("[1/4] Using sample data (offline mode)...")
        raw_tools = SAMPLE_TOOLS
    else:
        print("[1/4] Scraping live sources...")
        raw_tools = asyncio.run(scrape_all_sources())

    print(f"      → {len(raw_tools)} tools collected\n")

    # Step 2: Classify + enrich with LLM
    print(f"[2/4] Classifying tools with Groq LLM...")
    enriched_tools = process_tools(raw_tools, use_llm=use_llm)
    print(f"      → {len(enriched_tools)} tools classified\n")

    # Step 3: Save to DB
    print("[3/4] Saving to database...")
    clear_tools()  # Fresh run
    for tool in enriched_tools:
        save_tool(tool)
    print(f"      → {get_tool_count()} tools saved\n")

    # Step 4: Trend summary
    print("[4/4] Generating AI trend summary...")
    all_tools = get_all_tools()
    trend = generate_trend_summary(all_tools)
    print(f"\n📊 TREND SUMMARY:\n{trend}\n")

    log_run(len(enriched_tools), "success")

    print(f"{'='*50}")
    print(f"Pipeline complete! {len(enriched_tools)} tools processed.")
    print(f"{'='*50}\n")

    return enriched_tools


if __name__ == "__main__":
    import sys

    # Usage:
    #   python pipeline.py          → scrape live + use LLM
    #   python pipeline.py sample   → use sample data + use LLM
    #   python pipeline.py sample nokw → sample data, keyword only (no LLM)

    use_sample = "sample" in sys.argv
    use_llm = "nokw" not in sys.argv

    run_pipeline(use_sample_data=use_sample, use_llm=use_llm)
