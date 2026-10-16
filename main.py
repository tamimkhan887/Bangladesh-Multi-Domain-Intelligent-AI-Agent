import os
import sys
from pathlib import Path

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(ROOT_DIR / ".env", override=True)

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
try:
    from langchain.agents import create_tool_calling_agent, AgentExecutor
except ImportError:
    from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from tools.database_utils import get_llm
from tools import (
    InstitutionsDBTool,
    HospitalsDBTool,
    RestaurantsDBTool,
    WebSearchTool,
)

SYSTEM_PROMPT = """You are an intelligent, expert assistant specialized in Bangladesh information.
You have access to specialized database tools and a real-time web search tool.

ROUTING RULES:
1. 🧮 Data & Statistics Queries (Structured SQLite Databases):
   - Educational & Government Institutions: Route to `InstitutionsDBTool`
     (Use for universities, colleges, schools, madrasas, EIIN numbers, institution locations, and counts).
   - Healthcare Facilities & Hospitals: Route to `HospitalsDBTool`
     (Use for hospital counts, names, districts, divisions, government/private status, and facility statistics).
   - Restaurants & Dining: Route to `RestaurantsDBTool`
     (Use for restaurant names, ratings, locations, review counts, and dining statistics).

2. 🌐 General Knowledge & External Context:
   - Route to `WebSearchTool`
     (Use for government policies, laws, definitions, roles of organizations like DGHS or UGC, news, or any general information NOT present in the local database tables).

INSTRUCTIONS:
- Always choose the most specific tool for the query.
- Present answers in clear, concise, and professional natural language.
- Cite specific figures, names, or sources when available.
"""


def build_agent_executor(verbose: bool = True) -> AgentExecutor:
    """Build and return the Main AI Agent with LangChain AgentExecutor."""
    tools = [
        InstitutionsDBTool,
        HospitalsDBTool,
        RestaurantsDBTool,
        WebSearchTool,
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    llm = get_llm()
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
        handle_parsing_errors=True,
    )


def run_demo(executor: AgentExecutor):
    """Run demonstration queries covering DB tools and Web Search tool."""
    test_queries = [
        (
            "🧮 DB Query (Hospitals)",
            "How many hospitals are in Dhaka?",
        ),
        (
            "🧮 DB Query (Institutions)",
            "Give me top 3 colleges in Barisal division.",
        ),
        (
            "🧮 DB Query (Restaurants)",
            "What are 3 top-rated restaurants in Dhaka?",
        )
    ]

    print("\n" + "=" * 60)
    print("🚀 RUNNING MAIN AGENT DEMONSTRATION")
    print("=" * 60)

    for category, query in test_queries:
        print(f"\n--- {category} ---")
        print(f"User: {query}\n")
        try:
            response = executor.invoke({"input": query})
            print(f"\nFinal Answer:\n{response['output']}\n")
        except Exception as e:
            print(f"Error during execution: {e}\n")


def interactive_chat(executor: AgentExecutor):
    """Run an interactive console chat with the agent."""
    print("\n" + "=" * 60)
    print("🤖 BANGLADESH INTELLIGENT AGENT - INTERACTIVE MODE")
    print("Type your question below (or 'exit' / 'quit' to quit):")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit", "q"):
                print("Goodbye!")
                break

            response = executor.invoke({"input": user_input})
            print(f"\nAgent:\n{response['output']}")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting. Goodbye!")
            break
        except Exception as err:
            print(f"\nError: {err}")


if __name__ == "__main__":
    executor = build_agent_executor(verbose=True)

    if "--chat" in sys.argv or "-c" in sys.argv:
        interactive_chat(executor)
    else:
        # Default runs the demonstration of routing rules
        run_demo(executor)
