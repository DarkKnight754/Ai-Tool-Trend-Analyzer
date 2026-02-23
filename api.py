"""
api.py - FastAPI REST API
Run: uvicorn api:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from database import init_db, get_all_tools, get_category_stats, get_tool_count
from llm_engine import recommend_tool_for_task, generate_trend_summary
from typing import Optional

app = FastAPI(
    title="AI Tool TrendAnalyzer API",
    description="Scrapes, classifies, and recommends AI tools using Groq LLM",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {"message": "AI Tool TrendAnalyzer API", "tools": get_tool_count()}


@app.get("/tools")
def list_tools(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name/description"),
):
    """Get all tools with optional filters."""
    return {"tools": get_all_tools(category=category, search=search)}


@app.get("/stats")
def category_stats():
    """Get tool count per category."""
    return {"stats": get_category_stats(), "total": get_tool_count()}


@app.get("/recommend")
def recommend(task: str = Query(..., description="Describe what you want to do")):
    """Get AI-powered tool recommendation for a given task."""
    tools = get_all_tools()
    if not tools:
        return {"error": "No tools in database. Run the pipeline first."}
    result = recommend_tool_for_task(task, tools)
    return result


@app.get("/trends")
def trends():
    """Get AI-generated trend analysis."""
    tools = get_all_tools()
    summary = generate_trend_summary(tools)
    stats = get_category_stats()
    return {"summary": summary, "category_breakdown": stats}


@app.get("/categories")
def categories():
    """List all available categories."""
    stats = get_category_stats()
    return {"categories": list(stats.keys())}
