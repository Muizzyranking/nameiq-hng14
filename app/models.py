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
                age INTEGER NOT NULL,
                age_group TEXT NOT NULL,
                country_id TEXT NOT NULL,
                country_name TEXT NOT NULL,
                country_probability REAL NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_profiles_gender ON profiles(gender)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_profiles_age_group ON profiles(age_group)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_profiles_country_id ON profiles(country_id)"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_profiles_age ON profiles(age)")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON profiles(created_at)"
        )
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
    min_age: int | None = None,
    max_age: int | None = None,
    min_gender_probability: float | None = None,
    min_country_probability: float | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
    page: int = 1,
    limit: int = 10,
) -> tuple[list[dict[str, Any]], int]:
    """Return (profiles_list, total_count) for pagination metadata."""
    conn = get_connection()
    try:
        where_clauses: list[str] = []
        params: list[Any] = []

        if gender is not None:
            where_clauses.append("LOWER(gender) = LOWER(?)")
            params.append(gender)
        if country_id is not None:
            where_clauses.append("LOWER(country_id) = LOWER(?)")
            params.append(country_id)
        if age_group is not None:
            where_clauses.append("LOWER(age_group) = LOWER(?)")
            params.append(age_group)
        if min_age is not None:
            where_clauses.append("age >= ?")
            params.append(min_age)
        if max_age is not None:
            where_clauses.append("age <= ?")
            params.append(max_age)
        if min_gender_probability is not None:
            where_clauses.append("gender_probability >= ?")
            params.append(min_gender_probability)
        if min_country_probability is not None:
            where_clauses.append("country_probability >= ?")
            params.append(min_country_probability)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        count_row = conn.execute(
            f"SELECT COUNT(*) as total FROM profiles WHERE {where_sql}",
            params,
        ).fetchone()
        total = count_row["total"] if count_row else 0

        allowed_sort = {"age", "created_at", "gender_probability"}
        if sort_by not in allowed_sort:
            sort_by = "created_at"
        order_sql = "ASC" if order.lower() == "asc" else "DESC"

        offset = (page - 1) * limit
        query = f"""
            SELECT * FROM profiles
            WHERE {where_sql}
            ORDER BY {sort_by} {order_sql}
            LIMIT ? OFFSET ?
        """
        params_with_pagination = params + [limit, offset]
        rows = conn.execute(query, params_with_pagination).fetchall()
        return [row_to_dict(row) for row in rows], total
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


def profile_exists_by_name(name: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT 1 FROM profiles WHERE LOWER(name) = LOWER(?)", (name,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()
