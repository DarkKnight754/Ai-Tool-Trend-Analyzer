"""
dashboard.py - AI Tool TrendAnalyzer Dashboard
Run: streamlit run dashboard.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
from database import init_db, get_all_tools, get_category_stats, get_tool_count
from llm_engine import recommend_tool_for_task, generate_trend_summary
from pipeline import run_pipeline

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Tool TrendAnalyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS — fixes sidebar sliding + full redesign ───────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global reset ── */
*, html, body { font-family: 'Outfit', sans-serif !important; }

.stApp {
    background: #07070e !important;
}

/* ── SIDEBAR — stable, no sliding ── */
section[data-testid="stSidebar"] {
    background: #0d0d1a !important;
    border-right: 1px solid rgba(99,102,241,0.15) !important;
}

section[data-testid="stSidebar"] > div:first-child {
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
}

/* ── Hide broken Material Icons text on cloud ── */
button[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapseButton"] {
    font-family: 'Material Icons' !important;
    font-size: 0 !important;
    color: transparent !important;
}

[data-testid="stSidebarCollapseButton"] svg,
[data-testid="collapsedControl"] svg {
    display: block !important;
}

/* ── Sidebar content styling ── */
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] label {
    color: #94a3b8 !important;
    font-size: 0.85rem !important;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
}

/* Sidebar button */
section[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    padding: 0.6rem 1rem !important;
    width: 100% !important;
    transition: all 0.2s !important;
    letter-spacing: 0.3px !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-1px) !important;
}

/* Sidebar radio + checkbox */
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] .stCheckbox label {
    color: #cbd5e1 !important;
    font-size: 0.85rem !important;
}

/* Sidebar selectbox + text input */
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: #13132a !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 0.85rem !important;
}

section[data-testid="stSidebar"] hr {
    border-color: rgba(99,102,241,0.15) !important;
    margin: 1rem 0 !important;
}

/* ── Main content area ── */
.main .block-container {
    padding: 1rem 1.5rem 3rem 1.5rem !important;
    max-width: 100% !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0d0d1a !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid rgba(99,102,241,0.15) !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-radius: 9px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    padding: 8px 20px !important;
    transition: all 0.2s !important;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    font-weight: 600 !important;
}

/* ── Plotly charts transparent bg ── */
.js-plotly-plot { background: transparent !important; }

/* ── Headings ── */
h1, h2, h3, h4 { color: #e2e8f0 !important; }

/* ── Dataframe ── */
.stDataFrame {
    border: 1px solid rgba(99,102,241,0.15) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

/* ── Spinner ── */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* ── Success/Error/Info ── */
.stSuccess { background: rgba(16,185,129,0.1) !important; border-color: rgba(16,185,129,0.3) !important; }
.stError   { background: rgba(239,68,68,0.1) !important;  border-color: rgba(239,68,68,0.3) !important; }
.stInfo    { background: rgba(99,102,241,0.1) !important; border-color: rgba(99,102,241,0.3) !important; }

/* ── Primary button (main area) ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
    font-size: 0.95rem !important;
}

/* ── Text area ── */
.stTextArea textarea {
    background: #0d0d1a !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
}

.stTextArea textarea:focus {
    border-color: rgba(99,102,241,0.6) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #07070e; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.4); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Init ──────────────────────────────────────────────────────────────────────
init_db()

CATEGORY_COLORS = {
    "Code Generation":     "#6366f1",
    "Image Generation":    "#f59e0b",
    "Video Generation":    "#ef4444",
    "Audio & Speech":      "#10b981",
    "Data Analysis":       "#3b82f6",
    "Writing & Content":   "#8b5cf6",
    "Automation & Agents": "#f97316",
    "Search & Research":   "#06b6d4",
    "Chatbot & Assistant": "#ec4899",
    "Other":               "#64748b",
}

CATEGORY_ICONS = {
    "Code Generation":     "💻",
    "Image Generation":    "🎨",
    "Video Generation":    "🎬",
    "Audio & Speech":      "🎙️",
    "Data Analysis":       "📊",
    "Writing & Content":   "✍️",
    "Automation & Agents": "⚙️",
    "Search & Research":   "🔍",
    "Chatbot & Assistant": "💬",
    "Other":               "🔮",
}


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — fixed, never slides
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:

    # Logo / brand
    st.markdown("""
    <div style="padding:16px 0 20px 0; border-bottom:1px solid rgba(99,102,241,0.15); margin-bottom:20px;">
        <div style="font-size:1.5rem; font-weight:800; background:linear-gradient(135deg,#6366f1,#a78bfa);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            ⚡ TrendAnalyzer
        </div>
        <div style="color:#475569; font-size:0.75rem; margin-top:4px; letter-spacing:1px; text-transform:uppercase;">
            AI Tools Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Pipeline section ──
    st.markdown("**🚀 PIPELINE**")
    mode = st.radio(
        "Source",
        ["📦 Sample Data", "🌐 Live Scraping"],
        label_visibility="collapsed",
    )
    use_llm = st.checkbox("Use Groq LLM enrichment", value=True)

    run_clicked = st.button("▶  Run Pipeline", use_container_width=True)
    if run_clicked:
        use_sample = "Sample" in mode
        with st.spinner("Running..."):
            try:
                run_pipeline(use_sample_data=use_sample, use_llm=use_llm)
                st.success("Done!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    st.markdown("<hr>", unsafe_allow_html=True)

    # ── Filters section ──
    st.markdown("**🔍 FILTERS**")
    stats = get_category_stats()
    cats = ["All"] + list(stats.keys())
    selected_cat = st.selectbox("Category", cats, label_visibility="collapsed")
    search_term  = st.text_input("Search", placeholder="Search tools...", label_visibility="collapsed")




# ══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ══════════════════════════════════════════════════════════════════════════════

# ── Compact static header ────────────────────────────────────────────────────
st.markdown("""
<div style="padding:10px 0 8px 0; display:flex; align-items:center; gap:10px;">
    <div style="width:3px; height:26px; background:linear-gradient(180deg,#6366f1,#a78bfa); border-radius:2px; flex-shrink:0;"></div>
    <div>
        <div style="font-size:1.25rem; font-weight:800; line-height:1.1;
                    background:linear-gradient(135deg,#e2e8f0,#a78bfa);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            ⚡ AI Tool TrendAnalyzer
        </div>
        <div style="color:#475569; font-size:0.73rem; margin-top:1px;">
            Web Scraping × Groq LLM × Hybrid Classification
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Metric cards — single HTML block, always 4 columns, never cut off ──────
stats    = get_category_stats()
total    = get_tool_count()
top_cat  = max(stats, key=stats.get) if stats else "—"
n_cats   = len(stats)
top_icon = CATEGORY_ICONS.get(top_cat, "🔮")

st.markdown(f"""
<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-bottom:16px;">

  <div style="background:#0d0d1a; border:1px solid #6366f122;
              border-left:3px solid #6366f1; border-radius:10px; padding:10px 14px;">
    <div style="font-size:0.6rem; color:#475569; text-transform:uppercase; letter-spacing:1px;">Tools Indexed</div>
    <div style="font-size:1.3rem; font-weight:800; color:#6366f1; margin-top:3px;">{total}</div>
  </div>

  <div style="background:#0d0d1a; border:1px solid #10b98122;
              border-left:3px solid #10b981; border-radius:10px; padding:10px 14px;">
    <div style="font-size:0.6rem; color:#475569; text-transform:uppercase; letter-spacing:1px;">Categories</div>
    <div style="font-size:1.3rem; font-weight:800; color:#10b981; margin-top:3px;">{n_cats}</div>
  </div>

  <div style="background:#0d0d1a; border:1px solid #f59e0b22;
              border-left:3px solid #f59e0b; border-radius:10px; padding:10px 14px;
              overflow:hidden;">
    <div style="font-size:0.6rem; color:#475569; text-transform:uppercase; letter-spacing:1px;">Top Category</div>
    <div style="font-size:1.1rem; font-weight:800; color:#f59e0b; margin-top:3px;
                white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
      {top_icon} {top_cat}
    </div>
  </div>

  <div style="background:#0d0d1a; border:1px solid #ec489922;
              border-left:3px solid #ec4899; border-radius:10px; padding:10px 14px;">
    <div style="font-size:0.6rem; color:#475569; text-transform:uppercase; letter-spacing:1px;">LLM Engine</div>
    <div style="font-size:1.3rem; font-weight:800; color:#ec4899; margin-top:3px;">LLaMA 3.1</div>
  </div>

</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "  📊  Analytics  ",
    "  🔧  Tool Explorer  ",
    "  🤖  AI Recommend  ",
    "  📈  Trends  ",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Analytics
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not stats:
        st.markdown("""
        <div style="text-align:center; padding:60px 20px; color:#475569;">
            <div style="font-size:3rem; margin-bottom:16px;">📭</div>
            <div style="font-size:1.1rem; font-weight:600; color:#64748b;">No data yet</div>
            <div style="font-size:0.9rem; margin-top:8px;">Run the pipeline from the sidebar to get started</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        tools = get_all_tools()
        df    = pd.DataFrame(tools)

        # Row 1: pie + bar
        c1, c2 = st.columns([1, 1.2], gap="medium")

        with c1:
            st.markdown("<p style='color:#94a3b8; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>DISTRIBUTION</p>", unsafe_allow_html=True)
            fig_pie = go.Figure(go.Pie(
                labels=list(stats.keys()),
                values=list(stats.values()),
                hole=0.6,
                marker=dict(colors=[CATEGORY_COLORS.get(k, "#64748b") for k in stats.keys()],
                            line=dict(color="#07070e", width=2)),
                textinfo="percent",
                hovertemplate="<b>%{label}</b><br>%{value} tools<br>%{percent}<extra></extra>",
            ))
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Outfit"),
                showlegend=True,
                legend=dict(font=dict(color="#64748b", size=11), bgcolor="rgba(0,0,0,0)"),
                margin=dict(t=10, b=10, l=10, r=10),
                height=320,
                annotations=[dict(text=f"<b>{total}</b><br>tools", x=0.5, y=0.5,
                                  font=dict(size=16, color="#e2e8f0"), showarrow=False)],
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

        with c2:
            st.markdown("<p style='color:#94a3b8; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; margin-bottom:4px;'>TOOLS PER CATEGORY</p>", unsafe_allow_html=True)
            sorted_stats = dict(sorted(stats.items(), key=lambda x: x[1]))
            fig_bar = go.Figure(go.Bar(
                x=list(sorted_stats.values()),
                y=list(sorted_stats.keys()),
                orientation="h",
                marker=dict(
                    color=[CATEGORY_COLORS.get(k, "#64748b") for k in sorted_stats.keys()],
                    opacity=0.85,
                    line=dict(width=0),
                ),
                hovertemplate="<b>%{y}</b><br>%{x} tools<extra></extra>",
                text=list(sorted_stats.values()),
                textposition="outside",
                textfont=dict(color="#64748b", size=11),
            ))
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#94a3b8", family="Outfit"),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(gridcolor="rgba(255,255,255,0.03)", tickfont=dict(size=11)),
                margin=dict(t=10, b=10, l=10, r=50),
                height=320,
                bargap=0.3,
            )
            st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

        # Row 2: Audience heatmap
        if "audience_fit" in df.columns:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#94a3b8; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;'>AUDIENCE FIT HEATMAP</p>", unsafe_allow_html=True)

            rows = []
            for _, row in df.iterrows():
                fit = row.get("audience_fit") or {}
                if isinstance(fit, str):
                    try: fit = json.loads(fit)
                    except: fit = {}
                for audience, score in fit.items():
                    rows.append({"Category": row.get("category","Other"),
                                 "Audience": audience.capitalize(), "Score": score})

            if rows:
                fit_df    = pd.DataFrame(rows)
                pivot     = fit_df.groupby(["Category","Audience"])["Score"].mean().reset_index()
                pivot_w   = pivot.pivot(index="Category", columns="Audience", values="Score").fillna(0)

                fig_heat = go.Figure(go.Heatmap(
                    z=pivot_w.values,
                    x=list(pivot_w.columns),
                    y=list(pivot_w.index),
                    colorscale=[[0,"#0d0d1a"],[0.5,"#6366f1"],[1,"#a78bfa"]],
                    hovertemplate="<b>%{y}</b> → %{x}<br>Score: %{z:.1f}<extra></extra>",
                    showscale=True,
                    zmin=0, zmax=10,
                ))
                fig_heat.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#94a3b8", family="Outfit"),
                    height=300,
                    margin=dict(t=10, b=10, l=10, r=10),
                    xaxis=dict(tickfont=dict(size=11)),
                    yaxis=dict(tickfont=dict(size=11)),
                )
                st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Tool Explorer
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    tools = get_all_tools(
        category=selected_cat if selected_cat != "All" else None,
        search=search_term or None,
    )

    # Stats row
    ca, cb, cc = st.columns(3)
    with ca:
        st.markdown(f"<div style='color:#6366f1; font-size:1.6rem; font-weight:800;'>{len(tools)}</div><div style='color:#475569; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;'>Tools Found</div>", unsafe_allow_html=True)
    with cb:
        cats_shown = len(set(t.get("category","") for t in tools))
        st.markdown(f"<div style='color:#10b981; font-size:1.6rem; font-weight:800;'>{cats_shown}</div><div style='color:#475569; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;'>Categories</div>", unsafe_allow_html=True)
    with cc:
        llm_count = sum(1 for t in tools if t.get("classification_method") == "hybrid")
        st.markdown(f"<div style='color:#f59e0b; font-size:1.6rem; font-weight:800;'>{llm_count}</div><div style='color:#475569; font-size:0.75rem; text-transform:uppercase; letter-spacing:1px;'>LLM Enriched</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    if not tools:
        st.markdown("""
        <div style="text-align:center; padding:40px; color:#475569;">
            <div style="font-size:2.5rem;">🔍</div>
            <div style="margin-top:12px;">No tools match your filters.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 2-column card grid using native Streamlit columns
        for i in range(0, len(tools), 2):
            row_tools = tools[i:i+2]
            cols = st.columns(2, gap="medium")
            for col, tool in zip(cols, row_tools):
                cat     = tool.get("category", "Other")
                color   = CATEGORY_COLORS.get(cat, "#64748b")
                icon    = CATEGORY_ICONS.get(cat, "🔮")
                tasks   = tool.get("best_for_tasks") or []
                conf    = tool.get("keyword_confidence", 0)
                cpct    = (str(round(float(conf)*100)) + "%") if conf else "—"
                name    = str(tool.get("name","")).replace("<","&lt;").replace(">","&gt;")
                desc    = str(tool.get("summary") or tool.get("description",""))[:160].replace("<","&lt;").replace(">","&gt;")
                src     = str(tool.get("source","?")).replace("<","&lt;").replace(">","&gt;")
                price   = str(tool.get("pricing_hint","?")).replace("<","&lt;").replace(">","&gt;")
                tbadges = "".join(
                    '<span style="display:inline-block;padding:2px 7px;border-radius:5px;font-size:0.67rem;'
                    'background:' + color + '18;color:' + color + ';border:1px solid ' + color + '30;'
                    'margin:2px 2px 2px 0;">' + str(t)[:28] + '</span>'
                    for t in tasks[:4]
                )
                card = (
                    '<div style="background:#0d0d1a;border:1px solid rgba(255,255,255,0.05);'
                    'border-left:3px solid ' + color + ';border-radius:12px;padding:16px;margin-bottom:12px;">'
                    '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">'
                    '<div style="flex:1;min-width:0;">'
                    '<div style="font-size:0.95rem;font-weight:700;color:#e2e8f0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + name + '</div>'
                    '<div style="font-size:0.7rem;color:' + color + ';margin-top:2px;">' + icon + ' ' + cat + '</div>'
                    '</div>'
                    '<div style="font-size:0.65rem;color:#334155;text-align:right;margin-left:8px;flex-shrink:0;">'
                    '<div>' + cpct + '</div><div style="color:#1e3a5f;">' + price + '</div>'
                    '</div></div>'
                    '<p style="color:#64748b;font-size:0.8rem;line-height:1.5;margin:0 0 8px 0;">' + desc + '</p>'
                    '<div style="margin-bottom:8px;">' + tbadges + '</div>'
                    '<div style="font-size:0.65rem;color:#334155;border-top:1px solid rgba(255,255,255,0.04);padding-top:8px;">'
                    '📦 ' + src + '</div>'
                    '</div>'
                )
                with col:
                    st.markdown(card, unsafe_allow_html=True)
# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — AI Recommend
# ══════════════════════════════════════════════════════════════════════════════
with tab3:

    st.markdown("""
    <div style="margin-bottom:24px;">
        <h3 style="font-size:1.3rem; font-weight:700; margin:0 0 6px 0;">🤖 Find the Right AI Tool</h3>
        <p style="color:#64748b; font-size:0.9rem; margin:0;">
            Describe what you want to do — our AI matches you to the best tool.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Example chips
    examples = [
        "🖼️ Generate product images",
        "💻 Help me write code",
        "✍️ Write SEO blog posts",
        "📊 Analyze my CSV data",
        "🎙️ Transcribe a podcast",
        "⚙️ Automate email workflow",
    ]

    st.markdown("<p style='color:#475569; font-size:0.78rem; text-transform:uppercase; letter-spacing:1px;'>QUICK EXAMPLES</p>", unsafe_allow_html=True)
    ex_cols = st.columns(len(examples))
    selected_example = None
    for col, ex in zip(ex_cols, examples):
        with col:
            if st.button(ex, key=f"ex_{ex}", use_container_width=True):
                selected_example = ex.split(" ", 1)[1]  # strip emoji

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # Task input
    default_val = selected_example or st.session_state.get("task_val", "")
    task_input = st.text_area(
        "Describe your task",
        value=default_val,
        placeholder="e.g. I want to build a Python web scraper and need help writing the code...",
        height=110,
        label_visibility="collapsed",
    )

    if selected_example:
        st.session_state["task_val"] = selected_example

    btn_col, _ = st.columns([1, 3])
    with btn_col:
        find_clicked = st.button("⚡ Find Best Tool", type="primary", use_container_width=True)

    if find_clicked:
        if not task_input.strip():
            st.warning("Please describe your task first.")
        else:
            all_tools = get_all_tools()
            if not all_tools:
                st.error("No tools in database. Run the pipeline first from the sidebar.")
            else:
                with st.spinner("Finding top 5 tools..."):
                    result = recommend_tool_for_task(task_input, all_tools)

                # ── Extract top 5 tools from result ──────────────────────────
                top5 = result.get("top5", [])

                # Fallback: if LLM/keyword only returned 1, build top5 from category match
                if not top5:
                    task_cat   = result.get("task_category", "")
                    rec_name   = result.get("recommended_tool", "")
                    alt_name   = result.get("alternative", "")
                    cat_tools  = [t for t in all_tools if t.get("category") == task_cat]
                    other_tools= [t for t in all_tools if t.get("category") != task_cat]
                    pool       = cat_tools + other_tools

                    # Put best match first, alternative second, rest follow
                    ordered = []
                    for name in [rec_name, alt_name]:
                        match = next((t for t in pool if t.get("name","").lower() == name.lower()), None)
                        if match and match not in ordered:
                            ordered.append(match)
                    for t in pool:
                        if t not in ordered:
                            ordered.append(t)

                    top5 = ordered[:5]

                method       = str(result.get("method", ""))
                method_label = "🤖 Groq LLM" if "groq" in method else "🔑 Keyword"
                task_cat     = str(result.get("task_category", "—"))

                # ── Header bar ───────────────────────────────────────────────
                st.markdown(
                    '<div style="margin-top:20px;margin-bottom:14px;display:flex;'
                    'align-items:center;justify-content:space-between;">'
                    '<div style="font-size:0.7rem;color:#6366f1;text-transform:uppercase;'
                    'letter-spacing:2px;">✦ Top 5 Recommended Tools</div>'
                    '<div style="font-size:0.7rem;color:#334155;">Task: <span style="color:#94a3b8;">'
                    + task_cat + '</span> &nbsp;|&nbsp; ' + method_label + '</div>'
                    '</div>',
                    unsafe_allow_html=True
                )

                # ── Render each of the 5 tool cards ──────────────────────────
                for rank, tool in enumerate(top5):
                    tname   = str(tool.get("name","")).replace("<","&lt;").replace(">","&gt;")
                    tcat    = str(tool.get("category","Other")).replace("<","&lt;").replace(">","&gt;")
                    tdesc   = str(tool.get("summary") or tool.get("description",""))[:160]
                    tdesc   = tdesc.replace("<","&lt;").replace(">","&gt;")
                    tprice  = str(tool.get("pricing_hint","?")).replace("<","&lt;").replace(">","&gt;")
                    tcolor  = CATEGORY_COLORS.get(tool.get("category",""), "#6366f1")
                    ticon   = CATEGORY_ICONS.get(tool.get("category",""), "🔮")
                    tasks   = tool.get("best_for_tasks") or []
                    tbadges = "".join(
                        '<span style="display:inline-block;padding:2px 7px;border-radius:5px;font-size:0.67rem;'
                        'background:' + tcolor + '18;color:' + tcolor + ';border:1px solid ' + tcolor + '30;'
                        'margin:2px 2px 2px 0;">' + str(t)[:28] + '</span>'
                        for t in tasks[:3]
                    )

                    # Rank badge — gold for #1, silver for #2, rest normal
                    if rank == 0:
                        rank_color = "#f59e0b"
                        rank_label = "🥇 Best Match"
                        border_top = "border-top:2px solid #f59e0b;"
                    elif rank == 1:
                        rank_color = "#94a3b8"
                        rank_label = "🥈 Runner Up"
                        border_top = "border-top:1px solid rgba(255,255,255,0.08);"
                    else:
                        rank_color = "#475569"
                        rank_label = f"#{rank+1}"
                        border_top = "border-top:1px solid rgba(255,255,255,0.04);"

                    card = (
                        '<div style="background:#0d0d1a;border:1px solid rgba(255,255,255,0.06);'
                        'border-left:3px solid ' + tcolor + ';' + border_top +
                        'border-radius:12px;padding:16px;margin-bottom:10px;">'

                        '<div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">'
                        '<div style="flex:1;min-width:0;">'
                        '<div style="display:flex;align-items:center;gap:8px;">'
                        '<span style="font-size:0.65rem;color:' + rank_color + ';font-weight:700;">' + rank_label + '</span>'
                        '</div>'
                        '<div style="font-size:1rem;font-weight:700;color:#e2e8f0;margin-top:3px;">' + tname + '</div>'
                        '<div style="font-size:0.7rem;color:' + tcolor + ';margin-top:2px;">' + ticon + ' ' + tcat + '</div>'
                        '</div>'
                        '<div style="font-size:0.65rem;color:#334155;text-align:right;flex-shrink:0;margin-left:12px;">'
                        + tprice +
                        '</div></div>'

                        '<p style="color:#64748b;font-size:0.8rem;line-height:1.5;margin:0 0 8px 0;">' + tdesc + '</p>'
                        '<div>' + tbadges + '</div>'
                        '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Trends
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    all_tools = get_all_tools()

    if not all_tools:
        st.markdown("""
        <div style="text-align:center; padding:60px; color:#475569;">
            <div style="font-size:3rem;">📈</div>
            <div style="margin-top:12px; font-size:1rem;">Run the pipeline first to generate trend analysis.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        t1, t2 = st.columns([2, 1], gap="large")

        with t1:
            st.markdown("<p style='color:#94a3b8; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;'>AI TREND ANALYSIS</p>", unsafe_allow_html=True)

            # Auto-generate on load using category stats (no button, no LLM call)
            if stats:
                total_t = sum(stats.values())
                sorted_cats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
                top3 = ", ".join([f"{c} ({v} tools)" for c, v in sorted_cats[:3]])
                least = sorted_cats[-1][0] if sorted_cats else "—"
                dominant = sorted_cats[0][0] if sorted_cats else "—"
                dominant_pct = round(sorted_cats[0][1] / total_t * 100) if sorted_cats else 0

                trend_text = (
                    f"{dominant} leads the landscape with {dominant_pct}% of all indexed tools, "
                    f"reflecting strong industry demand for AI-assisted productivity in that domain. "
                    f"The top 3 categories — {top3} — account for the majority of tools, "
                    f"suggesting the market is consolidating around a few high-impact use cases. "
                    f"Categories like {least} remain emerging, signaling early-stage opportunities "
                    f"where AI adoption is still gaining traction."
                )

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0d1117,#0d0d1a);
                            border:1px solid rgba(99,102,241,0.2);
                            border-left:3px solid #6366f1;
                            border-radius:14px; padding:24px;">
                    <div style="color:#475569; font-size:0.7rem; text-transform:uppercase;
                                letter-spacing:1px; margin-bottom:12px;">💡 Trend Insight</div>
                    <p style="color:#cbd5e1; line-height:1.8; font-size:0.95rem; margin:0;
                              font-style:italic;">{trend_text}</p>
                </div>
                """, unsafe_allow_html=True)

        with t2:
            st.markdown("<p style='color:#94a3b8; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px;'>CATEGORY BREAKDOWN</p>", unsafe_allow_html=True)
            if stats:
                total_tools = sum(stats.values())
                for cat, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                    color = CATEGORY_COLORS.get(cat, "#64748b")
                    icon  = CATEGORY_ICONS.get(cat, "🔮")
                    pct   = count / total_tools * 100
                    st.markdown(f"""
                    <div style="margin-bottom:10px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                            <span style="font-size:0.82rem; color:#94a3b8;">{icon} {cat}</span>
                            <span style="font-size:0.82rem; color:{color}; font-weight:600;">{count}</span>
                        </div>
                        <div style="background:#13132a; border-radius:4px; height:5px; overflow:hidden;">
                            <div style="background:{color}; width:{pct}%; height:100%; border-radius:4px;
                                        transition:width 0.5s ease;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
