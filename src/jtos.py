import sqlite3
import json

def create_sqlite_db():
    con = sqlite3.connect("symbols.sqlite")
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE symbols(
            name TEXT,
            file TEXT,
            type TEXT,
            line INTEGER
        )
        """
    )
    con.commit()
    cur.execute(
        """
        CREATE TABLE paths(
            path   TEXT
        )
        """
    )
    con.commit()
    con.close()

create_sqlite_db()

con = sqlite3.connect("symbols.sqlite")
cur = con.cursor()
with open("symbol.json") as f:
    j = json.loads(f.read())

    for s in j["symbols"]:
        print(s)

        cur.execute(
            """
            INSERT INTO symbols(name, file, type, line)
            VALUES (?, ?, ?, ?)
            """,
            [
                s.get("symbol"),
                s.get("file"),
                s.get("type"),
                s.get("line")
            ]
        )
    con.commit()
    for p in j["paths"]:
        cur.execute(
            """
            INSERT INTO paths(path)
            VALUES (?)
            """,
            [p]
        )
    con.commit()

    con.close()
