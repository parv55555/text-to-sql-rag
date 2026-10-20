"""
Database Manager for Text-to-SQL RAG System.
Handles schema introspection, foreign key relationship graphs, safe execution,
and custom file/CSV ingestion.
"""

import re
import time
import sqlite3
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import deque
import pandas as pd
from sqlalchemy import create_engine, inspect, text


class DatabaseManager:
    """Manages SQLite and SQLAlchemy database connections, schema extraction,

    relationship graph navigation, and safe query execution.
    """

    def __init__(self, db_path_or_url: str):
        self.db_path_or_url = str(db_path_or_url)
        if not self.db_path_or_url.startswith("sqlite:///") and not "://" in self.db_path_or_url:
            self.connection_url = f"sqlite:///{Path(self.db_path_or_url).resolve()}"
            self.is_sqlite = True
        else:
            self.connection_url = self.db_path_or_url
            self.is_sqlite = "sqlite" in self.connection_url.lower()

        self.engine = create_engine(self.connection_url)
        self._fk_graph: Optional[Dict[str, Set[str]]] = None
        self._schema_cache: Dict[str, Any] = {}

    def get_tables(self) -> List[str]:
        """Returns all table names in the database."""
        inspector = inspect(self.engine)
        return sorted(inspector.get_table_names())

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Returns structured metadata for a given table."""
        if table_name in self._schema_cache:
            return self._schema_cache[table_name]

        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        pk_constraint = inspector.get_pk_constraint(table_name)
        fks = inspector.get_foreign_keys(table_name)

        col_defs = []
        for col in columns:
            is_pk = col['name'] in (pk_constraint.get('constrained_columns') or [])
            col_defs.append({
                "name": col['name'],
                "type": str(col['type']),
                "nullable": col.get('nullable', True),
                "is_pk": is_pk
            })

        fk_defs = []
        for fk in fks:
            for constrained, referred in zip(fk['constrained_columns'], fk['referred_columns']):
                fk_defs.append({
                    "from_col": constrained,
                    "to_table": fk['referred_table'],
                    "to_col": referred
                })

        # Row count
        row_count = 0
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\""))
                row_count = res.scalar() or 0
        except Exception:
            pass

        schema_data = {
            "name": table_name,
            "columns": col_defs,
            "foreign_keys": fk_defs,
            "row_count": row_count
        }
        self._schema_cache[table_name] = schema_data
        return schema_data

    def get_all_foreign_keys(self) -> List[Dict[str, str]]:
        """Extracts all directional foreign key relationships across all tables."""
        all_fks = []
        for table in self.get_tables():
            meta = self.get_table_schema(table)
            for fk in meta["foreign_keys"]:
                all_fks.append({
                    "from_table": table,
                    "from_col": fk["from_col"],
                    "to_table": fk["to_table"],
                    "to_col": fk["to_col"]
                })
        return all_fks

    def build_fk_graph(self) -> Dict[str, Set[str]]:
        """Builds an undirected adjacency list of table connections via foreign keys."""
        if self._fk_graph is not None:
            return self._fk_graph

        graph: Dict[str, Set[str]] = {t: set() for t in self.get_tables()}
        fks = self.get_all_foreign_keys()
        for fk in fks:
            t1, t2 = fk["from_table"], fk["to_table"]
            if t1 in graph and t2 in graph:
                graph[t1].add(t2)
                graph[t2].add(t1)

        self._fk_graph = graph
        return graph

    def find_relationship_bridges(self, selected_tables: List[str]) -> Set[str]:
        """Relationship-Aware Graph Search:

        Given a list of retrieved tables, finds any intermediate junction tables
        needed to connect them, preventing broken joins.
        """
        graph = self.build_fk_graph()
        selected = set(selected_tables)
        if len(selected) <= 1:
            return selected

        all_needed = set(selected)
        tables_list = list(selected)

        # Find shortest path between every pair of selected tables
        for i in range(len(tables_list)):
            for j in range(i + 1, len(tables_list)):
                start, target = tables_list[i], tables_list[j]
                path = self._shortest_path(graph, start, target)
                if path:
                    all_needed.update(path)

        return all_needed

    def _shortest_path(self, graph: Dict[str, Set[str]], start: str, end: str) -> Optional[List[str]]:
        """Standard BFS to find the shortest path between two tables in the FK graph."""
        if start not in graph or end not in graph:
            return None
        if start == end:
            return [start]

        visited = {start}
        queue = deque([[start]])

        while queue:
            path = queue.popleft()
            node = path[-1]

            for neighbor in graph.get(node, []):
                if neighbor == end:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    def get_sample_rows(self, table_name: str, limit: int = 3) -> pd.DataFrame:
        """Retrieves top N sample rows from a table."""
        try:
            with self.engine.connect() as conn:
                query = text(f"SELECT * FROM \"{table_name}\" LIMIT :limit")
                df = pd.read_sql_query(query, conn, params={"limit": limit})
                return df
        except Exception:
            return pd.DataFrame()

    def get_ddl_and_context(self, tables: List[str], include_samples: bool = True) -> str:
        """Generates clean, readable schema DDL statements, relationship notes,

        and sample data representations for LLM prompt injection.
        """
        context_parts = []
        for table in tables:
            schema = self.get_table_schema(table)
            cols = []
            for c in schema["columns"]:
                pk_tag = " PRIMARY KEY" if c["is_pk"] else ""
                null_tag = "" if c["nullable"] else " NOT NULL"
                cols.append(f"  \"{c['name']}\" {c['type']}{pk_tag}{null_tag}")

            fks = []
            for fk in schema["foreign_keys"]:
                fks.append(f"  FOREIGN KEY (\"{fk['from_col']}\") REFERENCES \"{fk['to_table']}\"(\"{fk['to_col']}\")")

            table_def = f"CREATE TABLE \"{table}\" (\n" + ",\n".join(cols + fks) + "\n);"

            # Add sample data
            sample_text = ""
            if include_samples:
                sample_df = self.get_sample_rows(table, limit=2)
                if not sample_df.empty:
                    # Compact string representation
                    cols_str = ", ".join(sample_df.columns.tolist()[:6])
                    rows_summary = []
                    for _, row in sample_df.iterrows():
                        row_vals = [str(v)[:25] for v in row.values[:6]]
                        rows_summary.append("(" + ", ".join(row_vals) + ")")
                    sample_text = f"\n-- Sample values for {table} [{cols_str}]:\n-- " + "\n-- ".join(rows_summary)

            context_parts.append(table_def + sample_text)

        return "\n\n".join(context_parts)

    def is_safe_query(self, sql_query: str) -> Tuple[bool, str]:
        """SQL Guardrail: strictly permits read-only SELECT or WITH statements.

        Blocks destructive or schema-altering commands.
        """
        cleaned = sql_query.strip().strip(";").strip()
        # Remove single-line comments
        cleaned = re.sub(r"--.*", "", cleaned)
        # Remove multi-line comments
        cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
        cleaned = cleaned.strip()

        if not cleaned:
            return False, "Query is empty."

        # Check for first keyword
        match = re.match(r"^(\w+)", cleaned, re.IGNORECASE)
        if not match:
            return False, "Invalid SQL syntax."

        first_keyword = match.group(1).upper()
        allowed_keywords = {"SELECT", "WITH", "EXPLAIN"}

        if first_keyword not in allowed_keywords:
            return False, f"Forbidden SQL operation: '{first_keyword}'. Only read-only queries (SELECT, WITH) are permitted."

        # Scan for dangerous mutation keywords anywhere in query
        dangerous_patterns = [
            r"\bDROP\b", r"\bDELETE\b", r"\bUPDATE\b", r"\bINSERT\b",
            r"\bALTER\b", r"\bTRUNCATE\b", r"\bCREATE\b", r"\bREPLACE\b",
            r"\bGRANT\b", r"\bREVOKE\b", r"\bEXEC\b", r"\bEXECUTE\b",
            r"\bATTACH\b", r"\bDETACH\b", r"\bPRAGMA\b"
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, cleaned, re.IGNORECASE):
                word = pattern.replace(r"\b", "")
                return False, f"Security Guardrail: Disallowed keyword '{word}' detected."

        return True, "Safe"

    def execute_query(self, sql_query: str, max_rows: int = 1000) -> Tuple[Optional[pd.DataFrame], float, Optional[str]]:
        """Safely executes the SQL query, returns (DataFrame, execution_time_ms, error_message)."""
        is_safe, reason = self.is_safe_query(sql_query)
        if not is_safe:
            return None, 0.0, f"Security Error: {reason}"

        start_time = time.perf_counter()
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(sql_query), conn)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                if len(df) > max_rows:
                    df = df.iloc[:max_rows]

                return df, elapsed_ms, None
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            error_str = str(e)
            # Clean up SQLAlchemy wrapper noise to get the actual database message
            if "sqlite3.OperationalError" in error_str or "OperationalError" in error_str:
                error_clean = error_str.split("\n")[0]
            else:
                error_clean = error_str
            return None, elapsed_ms, error_clean

    def load_csv(self, uploaded_file_or_path, table_name: str) -> Tuple[bool, str]:
        """Loads a CSV into SQLite as a new table."""
        try:
            df = pd.read_csv(uploaded_file_or_path)
            # Sanitize column names
            df.columns = [re.sub(r"[^\w]", "_", str(col).strip()) for col in df.columns]
            clean_table_name = re.sub(r"[^\w]", "_", table_name.strip())

            df.to_sql(clean_table_name, self.engine, if_exists="replace", index=False)
            self._schema_cache.clear()
            self._fk_graph = None
            return True, f"Successfully loaded table '{clean_table_name}' ({len(df)} rows, {len(df.columns)} columns)."
        except Exception as e:
            return False, f"Failed to load CSV: {e}"
