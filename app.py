"""
Text-to-SQL RAG Studio - Advanced Retrieval-Augmented Generation with BYOK Support.
"""

import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.db_manager import DatabaseManager
from core.llm_factory import LLMFactory, PROVIDER_METADATA
from core.sql_generator import SQLGenerator
from data.setup_sample_db import init_all_databases, DATA_DIR

st.set_page_config(
    page_title="Text-to-SQL RAG Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    code, pre, .stCode {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Streamlit defaults cleanup */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 4rem;
        max-width: 1200px;
    }
    .stAppHeader { display: none; }

    /* ── Page header ─────────────────────── */
    .page-header {
        padding-bottom: 1.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 2rem;
    }
    .page-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #F1F5F9;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .page-subtitle {
        font-size: 0.9rem;
        color: #64748B;
        margin-top: 0.3rem;
    }
    .page-meta {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.7rem;
    }
    .meta-tag {
        display: inline-block;
        font-size: 0.75rem;
        font-weight: 500;
        color: #94A3B8;
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 6px;
        padding: 0.2rem 0.55rem;
    }
    .meta-tag.active {
        color: #34D399;
        background: rgba(16,185,129,0.08);
        border-color: rgba(52,211,153,0.25);
    }

    /* ── Section labels ──────────────────── */
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #475569;
        margin-bottom: 0.65rem;
    }

    /* ── Query chips ─────────────────────── */
    .chip-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin-bottom: 1.2rem;
    }

    /* Override Streamlit secondary buttons for chips */
    div[data-testid="stHorizontalBlock"] button {
        background: transparent !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
        color: #94A3B8 !important;
        font-size: 0.82rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 0.55rem 0.8rem !important;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.4 !important;
        transition: border-color 0.15s, color 0.15s !important;
    }
    div[data-testid="stHorizontalBlock"] button:hover {
        border-color: rgba(99,102,241,0.5) !important;
        color: #E2E8F0 !important;
        background: rgba(99,102,241,0.06) !important;
    }

    /* ── Primary action button ────────────── */
    div.stButton > button[kind="primary"] {
        background: #4F46E5 !important;
        color: #FFFFFF !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.4rem !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: none !important;
        transition: background 0.15s !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #4338CA !important;
    }

    /* ── Text area ────────────────────────── */
    div[data-baseweb="textarea"] {
        border-radius: 8px !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        background: rgba(15,23,42,0.6) !important;
    }
    div[data-baseweb="textarea"]:focus-within {
        border-color: #4F46E5 !important;
        box-shadow: 0 0 0 2px rgba(79,70,229,0.2) !important;
    }
    div[data-baseweb="textarea"] textarea {
        color: #E2E8F0 !important;
        font-size: 0.95rem !important;
    }

    /* ── KPI strip ────────────────────────── */
    .kpi-strip {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.75rem;
    }
    .kpi-box {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
    }
    .kpi-label {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #475569;
        margin-bottom: 0.35rem;
    }
    .kpi-val {
        font-size: 1.3rem;
        font-weight: 700;
        color: #E2E8F0;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 400;
    }
    .kpi-box.ok .kpi-val { color: #34D399; }
    .kpi-box.warn .kpi-val { color: #FBBF24; }
    .kpi-box.err .kpi-val { color: #F87171; }

    /* ── Insight box ──────────────────────── */
    .insight {
        border-left: 3px solid #4F46E5;
        padding: 0.75rem 1rem;
        background: rgba(79,70,229,0.07);
        border-radius: 0 8px 8px 0;
        margin-top: 1rem;
        font-size: 0.9rem;
        color: #CBD5E1;
        line-height: 1.6;
    }

    /* ── RAG table tags ───────────────────── */
    .rag-table-row {
        display: flex;
        align-items: flex-start;
        gap: 0.6rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .rag-tag {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 0.15rem 0.5rem;
        border-radius: 5px;
        white-space: nowrap;
        margin-top: 0.15rem;
    }
    .rag-tag.semantic {
        background: rgba(79,70,229,0.15);
        color: #818CF8;
        border: 1px solid rgba(79,70,229,0.25);
    }
    .rag-tag.bridge {
        background: rgba(245,158,11,0.12);
        color: #FBBF24;
        border: 1px solid rgba(245,158,11,0.25);
    }
    .rag-table-name {
        font-weight: 600;
        color: #E2E8F0;
        font-size: 0.9rem;
    }
    .rag-table-desc {
        font-size: 0.8rem;
        color: #64748B;
    }

    /* ── Empty state feature grid ─────────── */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.75rem;
        margin-top: 1.5rem;
    }
    .feature-box {
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px;
        padding: 1rem 1.1rem;
    }
    .feature-num {
        font-size: 0.72rem;
        font-weight: 700;
        color: #4F46E5;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.35rem;
    }
    .feature-name {
        font-size: 0.92rem;
        font-weight: 600;
        color: #E2E8F0;
        margin-bottom: 0.25rem;
    }
    .feature-desc {
        font-size: 0.82rem;
        color: #64748B;
        line-height: 1.55;
    }

    /* ── Divider ──────────────────────────── */
    hr.clean {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.08);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Bootstrap ─────────────────────────────────────────────────────────────────
init_all_databases()

if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""
if "query_result" not in st.session_state:
    st.session_state.query_result = None

# ── Sidebar (unchanged) ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔑 BYOK Credentials")
    st.caption("Bring Your Own Key — your key stays strictly in memory.")

    provider = st.selectbox(
        "AI Provider",
        options=LLMFactory.get_supported_providers(),
        index=0,
        help="Select the LLM provider you have an API key for."
    )

    prov_meta = PROVIDER_METADATA.get(provider, {})
    model_options = prov_meta.get("models", [])
    default_model = prov_meta.get("default_model", "")

    selected_model = st.selectbox(
        "Model",
        options=model_options,
        index=0 if default_model not in model_options else model_options.index(default_model)
    )

    api_key = st.text_input(
        f"{provider} API Key",
        type="password",
        placeholder="Paste your key here...",
        help=f"Get your key at: {prov_meta.get('key_url', '')}"
    )

    custom_base_url = None
    if provider == "Custom / OpenRouter":
        custom_base_url = st.text_input(
            "API Base URL",
            value="https://openrouter.ai/api/v1",
            help="OpenAI-compatible base URL."
        )

    col_t1, col_t2 = st.columns([1, 1])
    with col_t1:
        if st.button("🧪 Test Key", use_container_width=True):
            if not api_key:
                st.error("Please enter an API key.")
            else:
                with st.spinner("Validating..."):
                    success, msg = LLMFactory.test_connection(
                        provider=provider,
                        api_key=api_key,
                        model_name=selected_model,
                        base_url=custom_base_url
                    )
                    if success:
                        st.success("Key Verified! ✅")
                    else:
                        st.error(f"Error: {msg}")

    with col_t2:
        key_link = prov_meta.get("key_url", "")
        if key_link:
            st.link_button("Get API Key ↗", key_link, use_container_width=True)

    st.markdown("---")

    st.markdown("### 🗄️ Database Source")
    db_choice = st.radio(
        "Active Database",
        options=["🎵 Chinook (Music Store)", "🛒 E-Commerce (Retail)", "📁 Custom File Upload"],
        index=0
    )

    active_db_path = None
    custom_uploaded_name = None

    if db_choice == "🎵 Chinook (Music Store)":
        active_db_path = DATA_DIR / "chinook.db"
    elif db_choice == "🛒 E-Commerce (Retail)":
        active_db_path = DATA_DIR / "ecommerce.db"
    else:
        uploaded_file = st.file_uploader("Upload .db, .sqlite, or .csv", type=["db", "sqlite", "csv"])
        if uploaded_file is not None:
            upload_target = DATA_DIR / f"custom_{uploaded_file.name}"
            with open(upload_target, "wb") as f:
                f.write(uploaded_file.getbuffer())

            if uploaded_file.name.endswith(".csv"):
                custom_db_path = DATA_DIR / "custom_csv.db"
                temp_db = DatabaseManager(str(custom_db_path))
                table_name = Path(uploaded_file.name).stem
                temp_db.load_csv(upload_target, table_name)
                active_db_path = custom_db_path
                custom_uploaded_name = table_name
            else:
                active_db_path = upload_target
        else:
            st.info("Upload a file or choose one of the pre-loaded databases above.")
            active_db_path = DATA_DIR / "chinook.db"

    db_mgr = DatabaseManager(str(active_db_path))
    tables = db_mgr.get_tables()

    with st.expander(f"🔍 Schema Explorer ({len(tables)} tables)"):
        selected_tbl = st.selectbox("Inspect Table", options=tables)
        if selected_tbl:
            meta = db_mgr.get_table_schema(selected_tbl)
            st.caption(f"**Rows:** {meta['row_count']}")
            cols_df = pd.DataFrame(meta["columns"])
            st.dataframe(cols_df, use_container_width=True, hide_index=True)
            sample_df = db_mgr.get_sample_rows(selected_tbl, limit=3)
            if not sample_df.empty:
                st.caption("Sample Data:")
                st.dataframe(sample_df, use_container_width=True, hide_index=True)


# ── Page Header ────────────────────────────────────────────────────────────────
db_label = db_choice.split("(")[0].strip().replace("🎵 ", "").replace("🛒 ", "").replace("📁 ", "")

st.markdown(f"""
<div class="page-header">
    <div class="page-title">Text-to-SQL RAG Studio</div>
    <div class="page-subtitle">Translate natural language questions into safe, accurate SQL queries using Retrieval-Augmented Generation.</div>
    <div class="page-meta">
        <span class="meta-tag">{db_label} · {len(tables)} tables</span>
        <span class="meta-tag">{provider} / {selected_model}</span>
        <span class="meta-tag active">● Read-only sandbox</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Query Builder ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Quick start — click any query to fill the input</div>', unsafe_allow_html=True)

if "Chinook" in db_choice:
    sample_chips = [
        "Which customer spent the most money overall?",
        "Top 5 most popular genres by tracks sold",
        "Artist with the highest number of albums",
        "Monthly revenue breakdown for 2023",
        "Employees and their manager names",
        "Rock tracks longer than 5 minutes"
    ]
elif "E-Commerce" in db_choice:
    sample_chips = [
        "Total revenue by product category",
        "Customers with more than 1 order and their total spend",
        "Products with stock quantity below 50",
        "Average order value across all orders"
    ]
else:
    sample_chips = [
        f"Show top 10 records from {tables[0]}" if tables else "Count rows in each table"
    ]

# 3 columns of chip buttons
chip_cols = st.columns(3)
for i, q in enumerate(sample_chips):
    with chip_cols[i % 3]:
        if st.button(q, key=f"chip_{i}", use_container_width=True):
            st.session_state.selected_question = q
            st.rerun()

st.write("")

user_question = st.text_area(
    "Ask a question in plain English",
    value=st.session_state.selected_question,
    placeholder="e.g. Which customer bought the most rock tracks in Germany?",
    height=80
)

act_col1, act_col2, act_col3 = st.columns([2, 1.5, 1.5])
with act_col1:
    execute_btn = st.button("Generate & Execute SQL", type="primary", use_container_width=True)
with act_col2:
    auto_self_heal = st.checkbox(
        "Self-healing reflection",
        value=True,
        help="If the query fails, automatically attempt to fix it using the error message."
    )
with act_col3:
    st.caption(f"Dialect: SQLite 3.x · {'Reflection ON' if auto_self_heal else 'Reflection OFF'}")


# ── Execution ──────────────────────────────────────────────────────────────────
if execute_btn:
    if not api_key:
        st.error("No API key provided. Add one in the sidebar.")
    elif not user_question.strip():
        st.warning("Please enter a question before running.")
    else:
        try:
            with st.spinner("Running RAG pipeline..."):
                llm = LLMFactory.create_llm(
                    provider=provider,
                    api_key=api_key,
                    model_name=selected_model,
                    base_url=custom_base_url
                )
                generator = SQLGenerator(db_manager=db_mgr, llm=llm)
                result = generator.generate_and_execute(
                    question=user_question,
                    max_retries=2 if auto_self_heal else 0
                )
                st.session_state.query_result = result
        except Exception as e:
            st.error(f"Error: {e}")


# ── Results ────────────────────────────────────────────────────────────────────
res = st.session_state.query_result

if res is not None:
    has_error = res.get("error") is not None
    corrections = res.get("correction_history", [])
    df = res.get("dataframe")
    df_len = len(df) if df is not None else 0
    ret_tables = res.get("retrieved_tables", [])
    bridges = res.get("bridge_tables", [])

    if has_error:
        status_cls, status_txt = "err", "Failed"
    elif corrections:
        status_cls, status_txt = "warn", f"Healed ({len(corrections)}x)"
    else:
        status_cls, status_txt = "ok", "Success"

    st.markdown('<hr class="clean">', unsafe_allow_html=True)

    # KPI strip
    st.markdown(f"""
    <div class="kpi-strip">
        <div class="kpi-box">
            <div class="kpi-label">Query time</div>
            <div class="kpi-val">{res.get('execution_time_ms', 0)}<span class="kpi-sub"> ms</span></div>
        </div>
        <div class="kpi-box">
            <div class="kpi-label">Rows returned</div>
            <div class="kpi-val">{df_len}</div>
        </div>
        <div class="kpi-box">
            <div class="kpi-label">Tables used</div>
            <div class="kpi-val">{len(ret_tables)}<span class="kpi-sub"> ({len(bridges)} bridges)</span></div>
        </div>
        <div class="kpi-box {status_cls}">
            <div class="kpi-label">Status</div>
            <div class="kpi-val">{status_txt}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab_sql, tab_data, tab_viz, tab_rag = st.tabs([
        "SQL Query", "Results", "Chart", "RAG Inspector"
    ])

    with tab_sql:
        if has_error:
            st.error(f"Database error: {res['error']}")

        st.code(res["sql"], language="sql")

        if res.get("explanation"):
            st.markdown(f'<div class="insight">{res["explanation"]}</div>', unsafe_allow_html=True)

    with tab_data:
        if df is not None and not df.empty:
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="results.csv",
                mime="text/csv"
            )
        elif df is not None and df.empty:
            st.info("Query ran successfully but returned 0 rows.")
        else:
            st.error("No data — query failed.")

    with tab_viz:
        chart = res.get("chart")
        if chart is not None:
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info("No chart available. Charts are generated when results contain numeric and categorical or date columns.")

    with tab_rag:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("**Schema tables retrieved**")
            for tbl in ret_tables:
                is_bridge = tbl in bridges
                tag = 'bridge">bridge' if is_bridge else 'semantic">semantic'
                desc = "FK bridge auto-resolved" if is_bridge else "Matched by semantic similarity"
                st.markdown(f"""
                <div class="rag-table-row">
                    <span class="rag-tag {tag}</span>
                    <div>
                        <div class="rag-table-name">{tbl}</div>
                        <div class="rag-table-desc">{desc}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col_b:
            st.markdown("**Few-shot examples injected**")
            few_shots = res.get("few_shots_used", [])
            for fs in few_shots:
                with st.expander(fs["question"]):
                    st.code(fs["sql"], language="sql")
                    if fs.get("explanation"):
                        st.caption(fs["explanation"])

        st.markdown('<hr class="clean">', unsafe_allow_html=True)
        st.markdown("**Self-correction history**")
        if not corrections:
            st.success("No corrections needed — query passed on first attempt.")
        else:
            for c in corrections:
                with st.expander(f"Attempt {c['attempt']} — {c['error'][:80]}"):
                    st.code(c["failed_sql"], language="sql")
                    st.caption("The error above was fed back to the model to generate a corrected query.")

else:
    # Empty state — show pipeline architecture cleanly
    st.markdown('<hr class="clean">', unsafe_allow_html=True)
    st.markdown("**How it works**")
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-box">
            <div class="feature-num">Step 1</div>
            <div class="feature-name">Relationship-Aware Schema Linking</div>
            <div class="feature-desc">Semantic search ranks relevant tables, then a BFS graph traversal over foreign keys automatically includes junction bridge tables — preventing broken JOINs.</div>
        </div>
        <div class="feature-box">
            <div class="feature-num">Step 2</div>
            <div class="feature-name">Few-Shot Golden Query Injection</div>
            <div class="feature-desc">Verified question-to-SQL pairs are ranked by similarity and injected into the prompt to guide dialect-specific patterns like strftime, CTEs, and aggregations.</div>
        </div>
        <div class="feature-box">
            <div class="feature-num">Step 3</div>
            <div class="feature-name">LLM Synthesis</div>
            <div class="feature-desc">The selected model receives the retrieved schema DDL, sample rows, few-shot examples, and the question to produce a precise SQLite query.</div>
        </div>
        <div class="feature-box">
            <div class="feature-num">Step 4</div>
            <div class="feature-name">Self-Correction Feedback Loop</div>
            <div class="feature-desc">The query is executed in a read-only sandbox. If a syntax or column error occurs, the traceback is fed back to the LLM which re-generates a corrected version.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
