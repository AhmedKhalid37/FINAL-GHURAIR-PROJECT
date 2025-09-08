import os, sqlite3
def init(db_path: str, seed_sql_path: str):
    with open(seed_sql_path, "r", encoding="utf-8") as f:
        sql = f.read()
    con = sqlite3.connect(db_path)
    try:
        con.executescript(sql)
        con.commit()
        print(f"Initialized DB at {db_path}")
    finally:
        con.close()
if __name__ == "__main__":
    base = os.path.dirname(__file__)
    init(os.path.join(base, "erp_sample.db"), os.path.join(base, "seed_data.sql"))
