import sqlite3
from typing import Any

DB_PATH = "profiles.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                gender TEXT NOT NULL,
                gender_probability REAL NOT NULL,
                sample_size INTEGER NOT NULL,
                age INTEGER NOT NULL,
                age_group TEXT NOT NULL,
                country_id TEXT NOT NULL,
                country_probability REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def insert_profile(profile: dict[str, Any]) -> None:
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO profiles (
                id, name, gender, gender_probability, sample_size,
                age, age_group, country_id, country_probability, created_at
            ) VALUES (
                :id, :name, :gender, :gender_probability, :sample_size,
                :age, :age_group, :country_id, :country_probability, :created_at
            )
            """,
            profile,
        )
        conn.commit()
    finally:
        conn.close()


def get_profile_by_id(profile_id: str) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (profile_id,)
        ).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def get_profile_by_name(name: str) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM profiles WHERE LOWER(name) = LOWER(?)", (name,)
        ).fetchone()
        return row_to_dict(row) if row else None
    finally:
        conn.close()


def get_all_profiles(
    gender: str | None = None,
    country_id: str | None = None,
    age_group: str | None = None,
) -> list[dict[str, Any]]:
    conn = get_connection()
    try:
        query = "SELECT * FROM profiles WHERE 1=1"
        params: list[str] = []

        if gender is not None:
            query += " AND LOWER(gender) = LOWER(?)"
            params.append(gender)
        if country_id is not None:
            query += " AND LOWER(country_id) = LOWER(?)"
            params.append(country_id)
        if age_group is not None:
            query += " AND LOWER(age_group) = LOWER(?)"
            params.append(age_group)

        rows = conn.execute(query, params).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()


def delete_profile_by_id(profile_id: str) -> bool:
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM profiles WHERE id = ?", (profile_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
