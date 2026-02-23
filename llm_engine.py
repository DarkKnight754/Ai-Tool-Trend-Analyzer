"""
llm_engine.py - Groq-powered LLM engine (FREE, no payment needed)
Handles classification, summarization, and recommendations
"""

import json
import os
import re
from groq import Groq
from typing import Dict, List

# ── Load .env file automatically ─────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Groq setup ────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if not GROQ_API_KEY or GROQ_API_KEY == "YOUR_GROQ_API_KEY_HERE":
    print("WARNING: GROQ_API_KEY not set! Recommendation will return fallback answers.")
    print("  Fix: Add GROQ_API_KEY=gsk_xxx to your .env file in the project folder.")
else:
    print(f"Groq API key loaded: {GROQ_API_KEY[:8]}...")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
MODEL = "llama-3.1-8b-instant"


# ── Categories ────────────────────────────────────────────────────────────────
CATEGORIES = [
    "Code Generation",
    "Image Generation",
    "Video Generation",
    "Audio & Speech",
    "Data Analysis",
    "Writing & Content",
    "Automation & Agents",
    "Search & Research",
    "Chatbot & Assistant",
    "Other",
]

# ── Keyword-based fallback recommendation (works WITHOUT Groq key) ───────────
TASK_KEYWORDS = {
    "Code Generation":      ["code", "coding", "programming", "developer", "debug", "script", "function", "github", "python", "javascript", "build app", "software"],
    "Image Generation":     ["image", "photo", "picture", "art", "illustration", "logo", "design", "visual", "draw", "generate image"],
    "Video Generation":     ["video", "animation", "movie", "clip", "reel", "youtube", "short film"],
    "Audio & Speech":       ["audio", "voice", "speech", "podcast", "transcribe", "tts", "music", "sound", "record"],
    "Data Analysis":        ["data", "analyse", "analyze", "analytics", "chart", "graph", "csv", "excel", "dashboard", "sql", "statistics", "insights"],
    "Writing & Content":    ["write", "writing", "blog", "article", "essay", "content", "seo", "copywrite", "social media", "caption"],
    "Automation & Agents":  ["automate", "automation", "workflow", "agent", "task", "schedule", "pipeline", "bot", "integrate"],
    "Search & Research":    ["search", "research", "find", "browse", "information", "fact", "knowledge", "answer"],
    "Chatbot & Assistant":  ["chat", "chatbot", "assistant", "conversation", "customer support", "help", "question"],
}

def keyword_recommend(task: str, available_tools: List[Dict]) -> Dict:
    """Fallback recommendation using keyword matching — works without Groq API.
    Returns top 5 tools ranked by category match."""
    task_lower = task.lower()

    # Score each category against the task
    scores = {}
    for cat, keywords in TASK_KEYWORDS.items():
        scores[cat] = sum(1 for kw in keywords if kw in task_lower)

    best_cat = max(scores, key=scores.get)
    if scores[best_cat] == 0:
        best_cat = "Chatbot & Assistant"

    # Sort tools: matching category first, then others
    cat_tools   = [t for t in available_tools if t.get("category") == best_cat]
    other_tools = [t for t in available_tools if t.get("category") != best_cat]
    ranked      = (cat_tools + other_tools)[:5]

    top_tool = ranked[0] if ranked else {}
    alt_tool = ranked[1] if len(ranked) > 1 else {}

    return {
        "recommended_tool": top_tool.get("name", "—"),
        "reason": (
            top_tool.get("name","") + " is the best match for your task under '"
            + best_cat + "'. "
            + str(top_tool.get("summary", top_tool.get("description","")))[:150]
        ),
        "alternative": alt_tool.get("name", "—"),
        "task_category": best_cat,
        "top5": ranked,
        "method": "keyword_fallback",
    }


def _call_groq(prompt: str, max_tokens: int = 512) -> str:
    """Call Groq API with automatic retry on rate limit (429)."""
    import time
    if not client:
        return "{}"
    for attempt in range(3):  # retry up to 3 times
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI tool analyst. Always respond with valid JSON only. No explanation, no markdown, just raw JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit" in err:
                wait = 3 * (attempt + 1)
                print(f"[LLM] Rate limit — waiting {wait}s (retry {attempt+1}/3)...")
                time.sleep(wait)
            else:
                print(f"[LLM] Groq API error: {e}")
                return "__FALLBACK__"
    print("[LLM] Rate limit retries exhausted — keyword fallback will be used")
    return "__FALLBACK__"


def _parse_json_safe(text: str) -> dict:
    """Safely parse JSON, stripping markdown fences if present."""
    text = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}


def classify_and_enrich_tool(name: str, description: str) -> Dict:
    """Classify tool using Groq LLM."""
    prompt = f"""
Analyze this AI tool and return a JSON object:

Tool Name: {name}
Description: {description}

Return this exact JSON structure:
{{
  "category": "one of {CATEGORIES}",
  "best_for_tasks": ["task1", "task2", "task3"],
  "summary": "A concise 1-2 sentence summary of what this tool does and who should use it.",
  "audience_fit": {{
    "developers": <score 1-10>,
    "designers": <score 1-10>,
    "marketers": <score 1-10>,
    "researchers": <score 1-10>,
    "businesses": <score 1-10>
  }},
  "tags": ["tag1", "tag2", "tag3"],
  "pricing_hint": "Free/Freemium/Paid/Open-source"
}}
"""
    raw = _call_groq(prompt)
    result = _parse_json_safe(raw)

    return {
        "category": result.get("category", "Other"),
        "best_for_tasks": result.get("best_for_tasks", []),
        "summary": result.get("summary", description[:200]),
        "audience_fit": result.get("audience_fit", {}),
        "tags": result.get("tags", []),
        "pricing_hint": result.get("pricing_hint", "Unknown"),
    }


def recommend_tool_for_task(task: str, available_tools: List[Dict]) -> Dict:
    """
    Recommend best tool for a task.
    Uses Groq LLM if key is available, otherwise falls back to keyword matching.
    """
    # ── Always fallback if no tools ──────────────────────────────────────────
    if not available_tools:
        return {"recommended_tool": "No tools", "reason": "Run pipeline first.", "alternative": "—", "task_category": "—", "method": "error"}

    # ── No API key → keyword fallback immediately ─────────────────────────────
    if not client or not GROQ_API_KEY:
        print("[LLM] No Groq key — using keyword recommendation")
        return keyword_recommend(task, available_tools)

    tool_list = "\n".join(
        [f"- {t['name']} ({t.get('category','?')}): {t.get('summary', t.get('description',''))[:120]}"
         for t in available_tools[:25]]
    )

    prompt = f"""
A user wants to accomplish this task: "{task}"

Here are available AI tools:
{tool_list}

Based on the task, pick the BEST tool from the list above.

Return ONLY this JSON (no extra text):
{{
  "recommended_tool": "<exact tool name from the list>",
  "reason": "<1-2 sentences explaining why this tool is best for this specific task>",
  "alternative": "<second best tool name from the list>",
  "task_category": "<category like Code Generation, Image Generation, Writing, etc>"
}}
"""
    raw = _call_groq(prompt, max_tokens=250)

    # Rate limited or errored → keyword fallback
    if raw == "__FALLBACK__" or not raw or raw == "{}":
        print("[LLM] Groq unavailable — using keyword fallback")
        return keyword_recommend(task, available_tools)

    result = _parse_json_safe(raw)
    if not result or not result.get("recommended_tool"):
        return keyword_recommend(task, available_tools)

    result["method"] = "groq_llm"
    return result


def generate_trend_summary(tools: List[Dict]) -> str:
    """Generate AI trend analysis from scraped tools."""
    categories = {}
    for t in tools:
        cat = t.get("category", "Other")
        categories[cat] = categories.get(cat, 0) + 1

    top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
    cat_summary = ", ".join([f"{k} ({v} tools)" for k, v in top_cats])

    if not client:
        return f"Based on {len(tools)} tools analyzed, the dominant categories are: {cat_summary}. AI tools are rapidly expanding across code generation, content creation, and automation domains."

    prompt = f"""
We scraped {len(tools)} AI tools. Top categories: {cat_summary}

Write a 3-sentence trend analysis about the current state of AI tools.
What categories dominate? What does this tell us about where AI is heading?
Return as plain text only, no JSON.
"""
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"AI tools are rapidly evolving. Top categories: {cat_summary}."


if __name__ == "__main__":
    result = classify_and_enrich_tool(
        "GitHub Copilot",
        "AI-powered code completion tool for developers using large language models."
    )
    print(json.dumps(result, indent=2))
