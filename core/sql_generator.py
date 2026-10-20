"""
SQL Generator & Self-Correction Engine.
Orchestrates:
1. RAG retrieval (Schema + Few-Shot)
2. Prompt formulation
3. LLM generation
4. SQL formatting & guardrail checks
5. Self-Correction & Reflection Loop (automatic healing on DB errors)
6. Natural language explanations & Auto-charting with Plotly
"""

import re
import time
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import sqlparse
import plotly.express as px
from langchain_core.messages import SystemMessage, HumanMessage

from core.db_manager import DatabaseManager
from core.rag_retriever import SchemaRetriever, FewShotRetriever


SYSTEM_PROMPT = """You are an elite Text-to-SQL Assistant and senior Database Architect.
Your task is to generate precise, highly-optimized, and valid SQL queries based on the user's natural language question and the provided database schema.

### Core Guidelines:
1. Dialect: SQLite. Use SQLite-compatible functions (e.g., strftime('%Y-%m', date_col), CAST, ROUND).
2. ONLY generate read-only queries (SELECT or WITH). Never generate DROP, DELETE, UPDATE, or INSERT.
3. Use the exact table names and column names as shown in the provided schema. Double-quote identifiers if necessary.
4. Ensure all JOIN conditions correctly match foreign keys to primary keys.
5. If the user asks for "top", "best", "highest", or "lowest", always use appropriate ORDER BY and LIMIT clauses.
6. Return ONLY the raw SQL query. Do not wrap in conversational chatter or apologies. You may use markdown code fences ```sql ... ```.
"""


class SQLGenerator:
    """Manages the full RAG pipeline: retrieval, prompt generation, LLM querying,

    self-correction loop, and visualization generation.
    """

    def __init__(self, db_manager: DatabaseManager, llm):
        self.db = db_manager
        self.llm = llm
        self.schema_retriever = SchemaRetriever(db_manager)
        self.few_shot_retriever = FewShotRetriever()

    def _extract_clean_sql(self, raw_text: str) -> str:
        """Strips markdown fences, explanations, and formats SQL cleanly."""
        text = raw_text.strip()
        # Look for ```sql ... ``` block
        match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            clean = match.group(1).strip()
        else:
            clean = text.strip()

        # Remove leading/trailing stray quotes or markdown
        clean = re.sub(r"^`+|`+$", "", clean).strip()

        # Format using sqlparse
        try:
            formatted = sqlparse.format(
                clean,
                reindent=True,
                keyword_case="upper",
                identifier_case="unchanged"
            )
            return formatted
        except Exception:
            return clean

    def _build_prompt(self, question: str, retrieved_tables: List[str], few_shots: List[Dict[str, str]]) -> str:
        """Assembles schema context, foreign key relationships, sample rows, and few-shots."""
        schema_context = self.db.get_ddl_and_context(retrieved_tables, include_samples=True)

        few_shot_sections = []
        for i, fs in enumerate(few_shots, 1):
            few_shot_sections.append(
                f"-- Example {i}:\n-- Question: {fs['question']}\n{fs['sql']}"
            )
        few_shots_text = "\n\n".join(few_shot_sections)

        prompt = f"""### Target Database Schema:
{schema_context}

### Verified Reference SQL Examples:
{few_shots_text}

### User Question:
{question}

Generate the exact SQLite SQL query to answer this question. Return ONLY the SQL query:"""
        return prompt

    def generate_and_execute(self, question: str, max_retries: int = 2) -> Dict[str, Any]:
        """Executes the complete Advanced RAG workflow with Self-Correction."""
        start_time = time.perf_counter()

        # 1. RAG Retrieval Step
        selected_tables, bridge_tables = self.schema_retriever.retrieve_tables(question, top_k=4, auto_bridge=True)
        few_shots = self.few_shot_retriever.retrieve_few_shots(question, top_k=2)

        # 2. Build Prompt
        prompt = self._build_prompt(question, selected_tables, few_shots)

        # 3. Initial LLM Call
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]

        llm_response = self.llm.invoke(messages)
        raw_output = llm_response.content if hasattr(llm_response, "content") else str(llm_response)
        current_sql = self._extract_clean_sql(raw_output)

        # 4. Safe Execution & Self-Correction Reflection Loop
        correction_history = []
        df = None
        exec_error = None
        exec_time = 0.0

        for attempt in range(max_retries + 1):
            df, exec_time, exec_error = self.db.execute_query(current_sql)

            if exec_error is None:
                # Query executed successfully!
                break

            # If error occurred and we have retries left, self-correct
            if attempt < max_retries:
                correction_entry = {
                    "attempt": attempt + 1,
                    "failed_sql": current_sql,
                    "error": exec_error
                }
                correction_history.append(correction_entry)

                # Formulate self-correction reflection prompt
                refinement_prompt = f"""The previous SQL query you generated produced an execution error on the database:
Database Error: {exec_error}

Invalid SQL Query:
{current_sql}

Relevant Database Schema:
{self.db.get_ddl_and_context(selected_tables, include_samples=False)}

Please analyze why this error occurred (check column names, table aliases, or join conditions) and output the CORRECTED SQLite query. Return ONLY the SQL:"""

                messages.append(HumanMessage(content=f"Attempt {attempt + 1} SQL:\n{current_sql}"))
                messages.append(HumanMessage(content=refinement_prompt))

                fix_response = self.llm.invoke(messages)
                fix_raw = fix_response.content if hasattr(fix_response, "content") else str(fix_response)
                current_sql = self._extract_clean_sql(fix_raw)

        total_latency = (time.perf_counter() - start_time) * 1000.0

        # 5. Natural Language Explanation & Auto-Chart
        explanation = ""
        chart = None

        if df is not None and not df.empty:
            explanation = self._generate_summary(question, current_sql, df)
            chart = self._create_auto_chart(df, question)
        elif df is not None and df.empty:
            explanation = "The query executed successfully, but returned 0 rows matching your criteria."

        return {
            "sql": current_sql,
            "dataframe": df,
            "execution_time_ms": round(exec_time, 2),
            "total_latency_ms": round(total_latency, 2),
            "error": exec_error,
            "retrieved_tables": selected_tables,
            "bridge_tables": bridge_tables,
            "few_shots_used": few_shots,
            "correction_history": correction_history,
            "explanation": explanation,
            "chart": chart
        }

    def _generate_summary(self, question: str, sql: str, df: pd.DataFrame) -> str:
        """Produces a brief, clear explanation of the query results."""
        row_count = len(df)
        cols = ", ".join(df.columns.tolist()[:4])
        preview_vals = []
        for col in df.columns[:2]:
            val = df[col].iloc[0]
            preview_vals.append(f"{col}: {val}")
        preview_str = ", ".join(preview_vals)

        return f"Returned **{row_count} row(s)** with columns `[{cols}]`. Top result: *{preview_str}*."

    def _create_auto_chart(self, df: pd.DataFrame, question: str):
        """Intelligently detects column types and creates an elegant Plotly visualization."""
        if df is None or len(df) < 1 or len(df.columns) < 2:
            return None

        # Exclude IDs or primary keys from charting when possible
        numeric_cols = [c for c in df.select_dtypes(include=["number"]).columns if not c.lower().endswith("id")]
        if not numeric_cols:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

        date_cols = [c for c in df.columns if any(k in c.lower() for k in ["date", "time", "month", "year", "day"])]
        cat_cols = [c for c in df.select_dtypes(include=["object", "string"]).columns if c not in date_cols]

        try:
            # Case 1: Temporal Trend (Date + Numeric) -> Line Chart
            if date_cols and numeric_cols:
                x_col = date_cols[0]
                y_col = numeric_cols[0]
                sorted_df = df.sort_values(by=x_col)
                fig = px.line(
                    sorted_df,
                    x=x_col,
                    y=y_col,
                    markers=True,
                    title=f"Trend: {y_col} over {x_col}",
                    template="plotly_dark",
                    color_discrete_sequence=["#6366F1"]
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=40, b=20))
                return fig

            # Case 2: Categorical Comparison (Category + Numeric) -> Bar Chart
            elif cat_cols and numeric_cols:
                x_col = cat_cols[0]
                y_col = numeric_cols[0]
                top_df = df.head(15)
                fig = px.bar(
                    top_df,
                    x=x_col,
                    y=y_col,
                    title=f"{y_col} by {x_col}",
                    template="plotly_dark",
                    color=y_col,
                    color_continuous_scale="Purp"
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=40, b=20))
                return fig

            # Case 3: Two Numeric Columns -> Scatter Plot
            elif len(numeric_cols) >= 2:
                fig = px.scatter(
                    df.head(50),
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f"{numeric_cols[1]} vs {numeric_cols[0]}",
                    template="plotly_dark",
                    color_discrete_sequence=["#10B981"]
                )
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=40, b=20))
                return fig

        except Exception:
            return None

        return None
