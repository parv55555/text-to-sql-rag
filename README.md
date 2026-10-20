# ⚡ Text-to-SQL RAG Studio

An enterprise-grade, interactive **Text-to-SQL Web Application** built with **Streamlit**, **Advanced RAG (Retrieval-Augmented Generation)**, and **BYOK (Bring Your Own Key)** multi-provider support.

---

## 🌟 Key Features

1. **BYOK Multi-Model Integration:**
   - Plug in your own API key for **Google Gemini**, **OpenAI**, **Anthropic Claude**, **Groq**, or **OpenRouter/Custom**.
   - Zero hardcoded keys; credentials remain strictly in memory within the current session.

2. **Advanced RAG Pipeline:**
   - **Relationship-Aware Schema Linking:** Uses semantic search to find candidate tables and a graph-traversal algorithm (BFS) to automatically include foreign-key bridge tables, preventing broken `JOIN` paths.
   - **Dynamic Few-Shot Gold Query Retrieval:** Indexes and retrieves the most relevant verified `(Question, SQL)` pairs to guide complex SQL joins and dialect idiosyncrasies.
   - **Dual-Mode Embedding Engine:** Combines local `SentenceTransformers` with a fast fallback to ensure immediate execution with zero external embedding cost.

3. **Agentic Self-Correction & Reflection Loop:**
   - If an initial query triggers a database syntax or column error, the agent captures the execution traceback, reflects against the schema, and automatically heals the query.

4. **Security & Guardrails:**
   - Strict read-only enforcement (`SELECT` / `WITH`). Prohibits mutating operations (`DROP`, `DELETE`, `UPDATE`, `ALTER`, `TRUNCATE`).

5. **Visual Analytics & Data Export:**
   - Interactive data table preview with 1-click CSV download.
   - Automatic column-type detection to render Plotly charts (Line trends, Bar comparisons, Scatter plots).

6. **Full RAG Transparency Inspector:**
   - Visual inspectability into retrieved tables, foreign-key bridges, few-shot examples used, and self-correction attempts.

---

## 📂 Project Structure

```
text-to-sql-rag/
├── app.py                      # Main Streamlit web application
├── core/
│   ├── __init__.py
│   ├── db_manager.py           # Schema introspection, FK graph search, safe execution
│   ├── llm_factory.py          # BYOK multi-provider LLM initialization & key testing
│   ├── rag_retriever.py        # Schema table retriever + Few-shot gold query retriever
│   └── sql_generator.py        # Prompt synthesis, self-correction loop, auto-charting
├── data/
│   ├── setup_sample_db.py      # Script to seed Chinook and E-Commerce SQLite databases
│   ├── chinook.db              # 11-table relational music store database
│   └── ecommerce.db            # 5-table e-commerce / retail database
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Streamlit App
```bash
streamlit run app.py
```

### 3. Using the App
1. Open the sidebar and choose your **AI Provider** (e.g., Google Gemini, OpenAI, Groq).
2. Enter your **API Key** and click **Test Key** to verify.
3. Select an **Active Database** (Chinook, E-Commerce, or upload your own CSV/SQLite file).
4. Click one of the suggested query chips or type a question in natural language.
5. Click **🚀 Generate & Execute SQL** to view results, charts, and RAG logs!
