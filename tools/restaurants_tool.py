import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from tools.database_utils import create_db_tool

RestaurantsDBTool = create_db_tool(
    tool_name="RestaurantsDBTool",
    description=(
        "Search the Bangladesh restaurants database. "
        "Use for questions about restaurant names, locations, "
        "cuisine types, ratings, prices, and restaurant counts "
        "when the corresponding fields exist."
    ),
    db_name="restaurants.db",
    table_name="restaurants",
    domain="Restaurants and food businesses in Bangladesh",
)


if __name__ == "__main__":
    print("[*] Testing RestaurantsDBTool...")
    result = RestaurantsDBTool.invoke("How many restaurants are in Dhaka?")
    print(result)
