import os
import json
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_openai import ChatOpenAI

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "databases"

load_dotenv(BASE_DIR / ".env", override=True)

_llm_instance = None

def get_llm():
    global _llm_instance
    if _llm_instance is None:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing credentials: OPENROUTER_API_KEY is not set. "
                "Please add your OpenRouter API key to the .env file: "
                "OPENROUTER_API_KEY=sk-or-v1-..."
            )
        _llm_instance = ChatOpenAI(
            model="nvidia/nemotron-3.5-super-vl:free",
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
        )
    return _llm_instance


class _LazyLLM:
    """Proxy to avoid crashing on import before environment variables are configured."""
    def __getattr__(self, name):
        return getattr(get_llm(), name)


llm = _LazyLLM()



def query_database(
    db_name: str,
    table_name: str,
    question: str,
    domain: str,
) -> str:
    db_path = DB_DIR / db_name

    if not db_path.exists():
        return f"Error: Database '{db_name}' was not found."

    try:
        # Open SQLite in read-only mode.
        connection = sqlite3.connect(
            f"{db_path.resolve().as_uri()}?mode=ro",
            uri=True,
            timeout=5,
        )
        connection.row_factory = sqlite3.Row

        try:
            connection.execute("PRAGMA query_only = ON")

            # Read the actual table schema.
            schema_rows = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()

            if not schema_rows:
                return f"Error: Table '{table_name}' was not found."

            schema = "\n".join(
                f"- {row['name']}: {row['type'] or 'UNKNOWN'}"
                for row in schema_rows
            )

            # Ask the model to generate SQL, not execute it.
            sql_response = llm.invoke(
                f"""
You are an expert SQLite query generator.

Database table: {table_name}
Domain: {domain}

Available columns:
{schema}

User question:
{question}

Rules:
1. Generate exactly one SQLite SELECT statement.
2. Use only the specified table and its listed columns.
3. Never use INSERT, UPDATE, DELETE, DROP, ALTER,
   CREATE, ATTACH, DETACH, or PRAGMA in the generated query.
4. Do not guess columns that are not listed.
5. Use case-insensitive matching for text when appropriate.
6. Use COUNT, AVG, SUM, MIN, MAX, GROUP BY, or ORDER BY
   when needed.
7. For ordinary lists, return at most 20 rows.
8. Do not invent data.
9. Return only SQL, without Markdown fences or explanations.
"""
            )

            sql = sql_response.content.strip()

            # Remove optional Markdown code fences and trailing semicolons.
            sql = re.sub(r"^```(?:sql)?\s*", "", sql, flags=re.I)
            sql = re.sub(r"\s*```$", "", sql).strip()
            sql = sql.rstrip(";").strip()

            # Basic read-only validation.
            if not re.match(r"^SELECT\b", sql, flags=re.I):
                return "I could not create a valid read-only SQL query."

            # Reject multiple statements and SQL comments.
            if ";" in sql or "--" in sql or "/*" in sql:
                return "The generated SQL query was rejected for safety."

            # Restrict queries to the intended table.
            # This also prevents querying SQLite system tables.
            referenced_tables = re.findall(
                r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                sql,
                flags=re.I,
            )

            if not referenced_tables or any(
                name.lower() != table_name.lower()
                for name in referenced_tables
            ):
                return "The generated SQL referenced an unauthorized table."

            # Execute SQL against the selected database.
            cursor = connection.execute(sql)
            rows = [dict(row) for row in cursor.fetchmany(21)]

            if not rows:
                return "No matching records were found in the database."

            # Limit the data sent to the summarization model.
            rows = rows[:20]

        finally:
            connection.close()

        # Convert actual query results into natural language.
        answer = llm.invoke(
            f"""
Answer the user's question using only the database results below.

Domain: {domain}
Question: {question}
SQL executed: {sql}
Database results:
{json.dumps(rows, ensure_ascii=False, default=str)}

Instructions:
- Explain the result clearly and concisely.
- Preserve exact counts, prices, ratings, and names.
- Do not add facts that are absent from the results.
- If results contain a single aggregate count or average,
  explain that number directly.
- If no records are returned, state that no matching
  records were found.
"""
        )

        return answer.content

    except sqlite3.Error as error:
        return f"Database query failed: {error}"

    except Exception as error:
        return f"Unable to answer the database question: {error}"


def create_db_tool(
    tool_name: str,
    description: str,
    db_name: str,
    table_name: str,
    domain: str,
):
    @tool(tool_name, description=description)
    def database_tool(question: str) -> str:
        """Query the relevant database and explain the results."""
        return query_database(
            db_name=db_name,
            table_name=table_name,
            question=question,
            domain=domain,
        )

    return database_tool


if __name__ == "__main__":
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        print("[!] Warning: OPENROUTER_API_KEY is not set.")
        print("[i] Please set OPENROUTER_API_KEY in your .env file:")
        print("    OPENROUTER_API_KEY=sk-or-v1-...")
    else:
        print("[OK] Found OPENROUTER_API_KEY in environment.")
        print("[*] Testing model connection...")
        try:
            model = get_llm()
            print("[OK] Model initialized successfully!")
        except Exception as err:
            print(f"[!] Error initializing model: {err}")
