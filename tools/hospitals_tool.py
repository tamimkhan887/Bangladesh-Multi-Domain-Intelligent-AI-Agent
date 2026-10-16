import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.database_utils import create_db_tool


HospitalsDBTool = create_db_tool(
    tool_name="HospitalsDBTool",
    description=(
        "Search the Bangladesh hospitals database. "
        "Use for questions about hospital names, locations, "
        "hospital types, bed capacity, doctors, facilities, "
        "and hospital statistics when those fields exist."
    ),
    db_name="hospitals.db",
    table_name="hospitals",
    domain="Hospitals and healthcare facilities in Bangladesh",
)



if __name__ == "__main__":
    print("[*] Testing HospitalsDBTool...")
    result = HospitalsDBTool.invoke("How many hospitals are in Dhaka?")
    print(result)
