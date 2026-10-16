import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv(ROOT_DIR / ".env", override=True)


def _search_web(query: str) -> str:
    """Execute web search using Tavily if API key is present, otherwise DuckDuckGo."""
    tavily_key = os.getenv("TAVILY_API_KEY")

    if tavily_key:
        try:
            from langchain_tavily import TavilySearchResults
            tavily_tool = TavilySearchResults(max_results=5)
            results = tavily_tool.invoke(query)
            if results:
                formatted = []
                for item in results:
                    content = item.get("content", "")
                    url = item.get("url", "")
                    formatted.append(f"- {content}\n  Source: {url}")
                return "\n\n".join(formatted)
        except Exception as e:
            # Fall back to DuckDuckGo if Tavily encounters an error
            pass

    # Free fallback without requiring extra API keys
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        ddg = DuckDuckGoSearchRun()
        return ddg.invoke(query)
    except Exception as e:
        return f"Web search could not retrieve results: {e}"


@tool("WebSearchTool")
def WebSearchTool(query: str) -> str:
    """Search the web for general knowledge, news, government policies, healthcare guidelines,
    and external information not present in the local databases.
    Example questions: 'What is the healthcare policy in Bangladesh?', 'What is the role of DGHS?'
    """
    return _search_web(query)


if __name__ == "__main__":
    print("[*] Testing WebSearchTool...")
    output = WebSearchTool.invoke("What is the healthcare policy in Bangladesh?")
    print(output[:300])
