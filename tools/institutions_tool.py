import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.database_utils import create_db_tool


InstitutionsDBTool = create_db_tool(
    tool_name="InstitutionsDBTool",
    description=(
        "Search the Bangladesh institutions database. "
        "Use for questions about universities, colleges, "
        "government institutions, institution locations, "
        "institution types, and counts of institutions."
    ),
    db_name="institutions.db",
    table_name="institutions",
    domain="Bangladeshi educational and government institutions",
)


if __name__ == "__main__":
    print("[*] Testing InstitutionsDBTool...")
    result = InstitutionsDBTool.invoke("How many institutions are in Dhaka?")
    print(result)
