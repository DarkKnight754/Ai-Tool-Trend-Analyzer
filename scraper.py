"""
scraper.py - Dynamic web scraper using Playwright + httpx
Uses RELIABLE, publicly scrapeable sources:
- GitHub Awesome-AI-Tools list (markdown, always works)
- Hugging Face Spaces public API (no auth needed)
- There's An AI For That (Playwright fallback)
"""

import asyncio
import re
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict

# Playwright optional — not available on Streamlit Cloud
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# ── Expanded SAMPLE data (fallback + offline testing) ───────────────────────
SAMPLE_TOOLS = [
    {"name": "GitHub Copilot",    "description": "AI-powered code completion and suggestion tool for developers. Supports multiple programming languages and major IDEs like VS Code.", "source": "Sample"},
    {"name": "Midjourney",        "description": "AI image generation tool that creates stunning artwork from text prompts using diffusion models.", "source": "Sample"},
    {"name": "Jasper AI",         "description": "AI writing assistant for marketing copy, blog posts, SEO content, and social media captions.", "source": "Sample"},
    {"name": "Tableau AI",        "description": "Business intelligence platform with AI-powered analytics, data visualization, and dashboard creation.", "source": "Sample"},
    {"name": "Zapier AI",         "description": "Workflow automation platform that connects 6000+ apps and automates repetitive tasks without coding.", "source": "Sample"},
    {"name": "Perplexity AI",     "description": "AI-powered search engine that provides real-time answers with cited sources from the web.", "source": "Sample"},
    {"name": "ElevenLabs",        "description": "AI voice synthesis and cloning tool for hyper-realistic speech in 29 languages.", "source": "Sample"},
    {"name": "Runway ML",         "description": "AI video generation and editing platform for creating cinematic content from text or images.", "source": "Sample"},
    {"name": "Notion AI",         "description": "AI assistant inside Notion for summarizing, drafting, translating, and improving documents.", "source": "Sample"},
    {"name": "AutoGPT",           "description": "Autonomous AI agent that browses the web, writes code, and completes multi-step tasks automatically.", "source": "Sample"},
    {"name": "Hugging Face",      "description": "Open-source ML platform for sharing, discovering, and deploying NLP, vision, and audio models.", "source": "Sample"},
    {"name": "Whisper",           "description": "OpenAI open-source speech-to-text transcription model with multilingual support and high accuracy.", "source": "Sample"},
    {"name": "Stable Diffusion",  "description": "Open-source text-to-image AI model that generates detailed images from text descriptions locally.", "source": "Sample"},
    {"name": "LangChain",         "description": "Framework for building LLM-powered applications, agents, and pipelines with memory and tool integration.", "source": "Sample"},
    {"name": "Cursor",            "description": "AI-first code editor built on VS Code with built-in chat, code generation, and codebase understanding.", "source": "Sample"},
    {"name": "Otter.ai",          "description": "AI meeting assistant that records, transcribes, and summarizes meetings in real time.", "source": "Sample"},
    {"name": "Copy.ai",           "description": "AI content generation platform for product descriptions, ad copy, blog posts, and sales emails.", "source": "Sample"},
    {"name": "Synthesia",         "description": "AI video generation platform that creates professional videos with AI avatars from plain text.", "source": "Sample"},
    {"name": "Descript",          "description": "AI-powered audio and video editor that lets you edit media by editing text transcripts.", "source": "Sample"},
    {"name": "Tome",              "description": "AI-powered presentation tool that generates complete slide decks from a text prompt.", "source": "Sample"},
    {"name": "Codeium",           "description": "Free AI code completion and chat assistant supporting 70+ languages and 40+ editors.", "source": "Sample"},
    {"name": "Pika Labs",         "description": "AI video generation platform that transforms images and text into animated video clips.", "source": "Sample"},
    {"name": "Character.ai",      "description": "Platform for creating and chatting with AI characters with distinct personalities.", "source": "Sample"},
    {"name": "Murf AI",           "description": "AI voice generator for creating studio-quality voiceovers for videos, podcasts, and presentations.", "source": "Sample"},
    {"name": "Phind",             "description": "AI search engine and coding assistant specialized for developers and technical questions.", "source": "Sample"},
    {"name": "Consensus",         "description": "AI search engine for scientific research that summarizes findings from peer-reviewed papers.", "source": "Sample"},
    {"name": "Gamma",             "description": "AI-powered tool for creating beautiful presentations, documents, and webpages from a prompt.", "source": "Sample"},
    {"name": "Replit Ghostwriter","description": "AI coding assistant embedded in Replit IDE for code completion, explanation, and transformation.", "source": "Sample"},
    {"name": "Beautiful.ai",      "description": "AI presentation software with smart slide templates that auto-adjust design and layout.", "source": "Sample"},
    {"name": "Mem.ai",            "description": "AI-powered knowledge base that automatically organizes notes and surfaces relevant information.", "source": "Sample"},
]


# ── Source 1: GitHub Awesome List (most reliable — plain markdown) ───────────
async def scrape_github_awesome_list() -> List[Dict]:
    """
    Scrapes the curated 'Awesome AI Tools' GitHub README.
    GitHub raw markdown is always accessible — no JS, no auth, no blocking.
    """
    url = "https://raw.githubusercontent.com/mahseema/awesome-ai-tools/main/README.md"
    tools = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                print(f"[Scraper] GitHub list returned {resp.status_code}")
                return []

            for line in resp.text.split("\n"):
                # Match: - [Tool Name](url) - description
                match = re.match(r"\s*[-*]\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–:]\s*(.+)", line)
                if match:
                    name = match.group(1).strip()
                    desc = match.group(3).strip()
                    if len(name) > 2 and len(desc) > 15 and len(name) < 60:
                        tools.append({
                            "name": name,
                            "description": desc[:500],
                            "source": "GitHub Awesome AI Tools",
                        })

        print(f"[Scraper] Found {len(tools)} tools from GitHub Awesome List")
    except Exception as e:
        print(f"[Scraper] GitHub list error: {e}")

    return tools[:40]


# ── Source 2: Hugging Face Spaces public API (JSON, no auth needed) ──────────
async def scrape_huggingface_spaces() -> List[Dict]:
    """
    Uses HuggingFace public REST API — returns open AI spaces/apps in JSON.
    No API key required.
    """
    url = "https://huggingface.co/api/spaces?limit=30&sort=likes&direction=-1"
    tools = []

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                print(f"[Scraper] HuggingFace API returned {resp.status_code}")
                return []

            for space in resp.json():
                name = space.get("id", "").split("/")[-1].replace("-", " ").title()
                card = space.get("cardData") or {}
                desc = card.get("short_description", "")
                if not desc or len(desc) < 10:
                    tags = space.get("tags", [])
                    desc = f"AI tool on Hugging Face. Tags: {', '.join(tags[:5])}" if tags else "AI tool hosted on Hugging Face Spaces."
                if name:
                    tools.append({"name": name[:80], "description": desc[:500], "source": "Hugging Face Spaces"})

        print(f"[Scraper] Found {len(tools)} tools from Hugging Face")
    except Exception as e:
        print(f"[Scraper] HuggingFace error: {e}")

    return tools


# ── Source 3: There's An AI For That (Playwright — local only) ───────────────
async def scrape_theresanaiforthat() -> List[Dict]:
    """Playwright scraper — skipped automatically on Streamlit Cloud."""
    tools = []

    if not PLAYWRIGHT_AVAILABLE:
        print("[Scraper] Playwright not available (cloud mode) — skipping TAAFT")
        return []

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
            )
            page = await context.new_page()
            await page.route("**/*.{png,jpg,jpeg,gif,webp,woff,woff2}", lambda r: r.abort())
            await page.goto("https://theresanaiforthat.com", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            html = await page.content()
            await browser.close()

        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("article, div[class*='card'], div[class*='tool'], li[class*='tool']")[:25]:
            name_tag = card.find(["h2", "h3", "h4", "strong"])
            desc_tag = card.find("p")
            if name_tag and desc_tag:
                name = name_tag.get_text(strip=True)
                desc = desc_tag.get_text(strip=True)
                if 2 < len(name) < 80 and len(desc) > 15:
                    tools.append({"name": name, "description": desc[:500], "source": "There's An AI For That"})

        print(f"[Scraper] Found {len(tools)} tools from There's An AI For That")
    except Exception as e:
        print(f"[Scraper] TAAFT error: {e}")

    return tools


# ── Main entry point ──────────────────────────────────────────────────────────
async def scrape_all_sources() -> List[Dict]:
    """Run all scrapers, merge results, deduplicate. Falls back to sample data if needed."""
    all_tools = []

    # Concurrent HTTP scrapers
    print("[Scraper] Fetching GitHub Awesome List + HuggingFace API...")
    results = await asyncio.gather(
        scrape_github_awesome_list(),
        scrape_huggingface_spaces(),
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, list):
            all_tools.extend(r)

    # Playwright scraper
    print("[Scraper] Launching Playwright for There's An AI For That...")
    taaft = await scrape_theresanaiforthat()
    all_tools.extend(taaft)

    # Supplement with sample data if live scraping is sparse
    if len(all_tools) < 10:
        print(f"[Scraper] Only {len(all_tools)} live tools found — adding sample data as supplement")
        all_tools.extend(SAMPLE_TOOLS)

    # Deduplicate
    seen, unique = set(), []
    for t in all_tools:
        key = t["name"].lower().strip()
        if key not in seen and len(key) > 1:
            seen.add(key)
            unique.append(t)

    print(f"[Scraper] Total unique tools collected: {len(unique)}")
    return unique


if __name__ == "__main__":
    tools = asyncio.run(scrape_all_sources())
    print(f"\nTotal: {len(tools)}")
    for t in tools[:5]:
        print(f"  - {t['name']}: {t['description'][:80]}...")
