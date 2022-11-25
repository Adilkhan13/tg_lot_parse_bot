import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = "/src/database/main.db"
DB_PATH = os.path.abspath(DB_PATH)
DB_LAG = """select julianday(max(CURRENT_TIMESTAMP)) - julianday(max(created_date)) from goszakup_lots;"""


def delete_duplicates_from_sql():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    for sql in [
        "DELETE from samruk_lots WHERE id in(select id from samruk_lots GROUP BY id HAVING COUNT(*) >1);",
        "DELETE from goszakup_lots WHERE id in(select id from goszakup_lots GROUP BY id HAVING COUNT(*) >1);",
    ]:
        cur.execute(sql)
    con.commit()
    con.close()


def show_sql(sql):
    con = sqlite3.connect(DB_PATH)
    cursor = con.cursor()
    cursor.execute(sql)
    col_names = [i[0] for i in cursor.description]
    return cursor.fetchall()


def yesterday(resource: str, lag: int = 1) -> str:
    lag += 1
    if resource == "gz":
        yesterday = (datetime.today() - timedelta(days=lag)).strftime("%d.%m.%Y")
        yesterday = f"&filter%5Bstart_date_from%5D={yesterday}"
    elif resource == "sk":
        yesterday = (datetime.today() - timedelta(days=lag)).strftime("%Y-%m-%d")
    else:
        return None
    if yesterday:
        return yesterday
    else:
        today = str(datetime.today().strftime("%d.%m.%Y"))
        return f"&filter%5Bstart_date_from%5D={today}"


if __name__ == "__main__":
    delete_duplicates_from_sql()
