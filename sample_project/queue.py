"""Small queue prototype used to demonstrate code-grounded questions."""

import sqlite3

DATABASE = "campus_queue.db"


def reserve(student_name: str) -> int:
    with sqlite3.connect(DATABASE) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS reservations "
            "(id INTEGER PRIMARY KEY, student_name TEXT, status TEXT)"
        )
        cursor = connection.execute(
            "INSERT INTO reservations (student_name, status) VALUES (?, 'waiting')",
            (student_name,),
        )
        return cursor.lastrowid


def serve_next() -> str | None:
    with sqlite3.connect(DATABASE) as connection:
        row = connection.execute(
            "SELECT id, student_name FROM reservations "
            "WHERE status = 'waiting' ORDER BY id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        connection.execute(
            "UPDATE reservations SET status = 'served' WHERE id = ?",
            (row[0],),
        )
        return row[1]
