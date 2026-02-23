# AI Tool TrendAnalyzer
## Web Scraping + Generative AI (Groq — Free)

End-to-end pipeline that scrapes AI tool directories, classifies them using hybrid keyword + LLM classification, and provides tool recommendations.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Get your FREE Groq API key
- Visit: https://console.groq.com
- Sign up → Create API key (free, no credit card)
- Copy your key starting with `gsk_...`

### 3. Set environment variable
```bash
# Linux/Mac
export GROQ_API_KEY="gsk_your_key_here"

# Windows
set GROQ_API_KEY=gsk_your_key_here
```

### 4. Run the pipeline
```bash
# With sample data (no internet needed, good for testing)
python pipeline.py sample

# With live scraping
python pipeline.py
```

### 5. Launch dashboard
```bash
streamlit run dashboard.py
```

### 6. (Optional) Launch API
```bash
uvicorn api:app --reload
# API docs: http://localhost:8000/docs
```

---

## 📁 Project Structure

```
ai-tool-analyzer/
├── scraper.py       # Playwright dynamic scraping
├── classifier.py    # Hybrid keyword + LLM classification
├── llm_engine.py    # Groq API integration (LLaMA 3.1)
├── database.py      # SQLite storage
├── pipeline.py      # End-to-end pipeline orchestrator
├── api.py           # FastAPI REST API
├── dashboard.py     # Streamlit dashboard
└── requirements.txt
```

---

## 🧠 Architecture

```
[Dynamic Sites] → Playwright → BeautifulSoup
                                    ↓
                           Hybrid Classifier
                         ┌────────────────────┐
                         │ Keyword Rules (fast)│
                         │ + Groq LLM (smart) │
                         └────────────────────┘
                                    ↓
                              SQLite DB
                         ┌────────────────────┐
                         │ FastAPI REST API    │
                         │ Streamlit Dashboard │
                         └────────────────────┘
```

---

## 💡 Groq Free Tier
- **14,400 requests/day** on free plan
- Model: `llama-3.1-8b-instant`
- No credit card required
- ~100ms response time

---

## 🎯 Features
- ✅ Dynamic JS page scraping (Playwright)
- ✅ Hybrid classification (keyword + LLM)
- ✅ AI-powered tool recommendations
- ✅ Automated trend summarization
- ✅ Interactive dashboard with charts
- ✅ REST API with filtering
- ✅ 100% free (no paid APIs)
