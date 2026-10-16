import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")
DB_DIR = Path("databases")
DB_DIR.mkdir(exist_ok=True)

DATASETS = {
    "institutions": (
        DATA_DIR / "institutions.csv",
        DB_DIR / "institutions.db",
    ),
    "hospitals": (
        DATA_DIR / "hospitals.csv",
        DB_DIR / "hospitals.db",
    ),
    "restaurants": (
        DATA_DIR / "restaurants.csv",
        DB_DIR / "restaurants.db",
    ),
}


def convert_csv_to_sqlite(csv_path, db_path, table_name):
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    df = df.dropna(axis=1, how="all")

    with sqlite3.connect(db_path) as connection:
        df.to_sql(
            table_name,
            connection,
            if_exists="replace",
            index=False,
        )

        count = pd.read_sql_query(
            f'SELECT COUNT(*) AS total FROM "{table_name}"',
            connection,
        ).iloc[0]["total"]

    print(f"{db_path}: {count} rows, table={table_name}")
    print("Columns:", df.columns.tolist())


if __name__ == "__main__":
    for table_name, (csv_path, db_path) in DATASETS.items():
        convert_csv_to_sqlite(csv_path, db_path, table_name)