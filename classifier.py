"""
classifier.py - Hybrid keyword + LLM classification
Keyword rules run first (fast/free), LLM only for uncertain cases
"""

from typing import Dict, Tuple

# ── Keyword rules per category ────────────────────────────────────────────────
KEYWORD_RULES: Dict[str, list] = {
    "Code Generation":      ["code", "coding", "programming", "developer", "github", "copilot",
                              "IDE", "autocomplete", "refactor", "debugging", "python", "javascript"],
    "Image Generation":     ["image", "photo", "art", "picture", "illustration", "stable diffusion",
                              "dall-e", "midjourney", "text-to-image", "artwork", "visual", "generate image"],
    "Video Generation":     ["video", "animation", "movie", "film", "cinematic", "text-to-video",
                              "runway", "sora", "clip", "render"],
    "Audio & Speech":       ["audio", "voice", "speech", "tts", "transcription", "podcast",
                              "music", "sound", "whisper", "elevenlabs", "clone voice"],
    "Data Analysis":        ["data", "analytics", "dashboard", "chart", "sql", "csv", "excel",
                              "visualization", "bi", "insights", "statistics", "tableau"],
    "Writing & Content":    ["write", "writing", "blog", "seo", "copywriting", "content",
                              "essay", "article", "marketing copy", "social media", "jasper"],
    "Automation & Agents":  ["automate", "automation", "workflow", "agent", "pipeline",
                              "zapier", "n8n", "task", "autonomous", "schedule", "bot"],
    "Search & Research":    ["search", "research", "browse", "web", "real-time", "citation",
                              "knowledge", "perplexity", "question answering", "fact"],
    "Chatbot & Assistant":  ["chat", "chatbot", "assistant", "conversation", "customer service",
                              "support", "dialogue", "gpt", "claude", "gemini"],
}


def keyword_classify(text: str) -> Tuple[str, float]:
    """
    Score text against keyword rules.
    Returns (best_category, confidence_0_to_1)
    """
    text_lower = text.lower()
    scores = {}

    for category, keywords in KEYWORD_RULES.items():
        matched = sum(1 for kw in keywords if kw.lower() in text_lower)
        scores[category] = matched

    best_cat = max(scores, key=scores.get)
    best_score = scores[best_cat]

    total_possible = len(KEYWORD_RULES[best_cat])
    confidence = min(best_score / max(total_possible * 0.3, 1), 1.0)

    if best_score == 0:
        return "Other", 0.0

    return best_cat, round(confidence, 2)


def hybrid_classify(name: str, description: str, llm_fn=None) -> Dict:
    """
    Hybrid classification:
    - High keyword confidence → use keyword result, skip LLM call (saves quota)
    - Low confidence → call LLM for accurate classification + full enrichment
    """
    combined_text = f"{name} {description}"
    keyword_cat, confidence = keyword_classify(combined_text)

    # High confidence: keyword is reliable, still enrich with LLM
    if confidence >= 0.4 and llm_fn:
        llm_result = llm_fn(name, description)
        # Override LLM category with keyword result if confidence is high
        if confidence >= 0.6:
            llm_result["category"] = keyword_cat
        llm_result["classification_method"] = "hybrid"
        llm_result["keyword_confidence"] = confidence
        return llm_result

    # Medium/low confidence: let LLM decide everything
    if llm_fn:
        llm_result = llm_fn(name, description)
        llm_result["classification_method"] = "llm"
        llm_result["keyword_confidence"] = confidence
        return llm_result

    # No LLM available: keyword only
    return {
        "category": keyword_cat,
        "best_for_tasks": [],
        "summary": description[:200],
        "audience_fit": {},
        "tags": [],
        "pricing_hint": "Unknown",
        "classification_method": "keyword_only",
        "keyword_confidence": confidence,
    }


if __name__ == "__main__":
    # Test without LLM
    result = hybrid_classify(
        "GitHub Copilot",
        "AI-powered code completion and suggestion tool for developers"
    )
    print(result)
