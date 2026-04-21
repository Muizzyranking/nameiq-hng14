import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import uuid6

from countries import get_country_name
from models import get_connection, init_db, profile_exists_by_name
from services import classify_age_group

DATA_PATH = Path(__file__).parent / "data" / "profiles.json"


def load_profiles() -> list[dict[str, Any]]:
    if not DATA_PATH.exists():
        print(f"Error: {DATA_PATH} not found. Please place the seed file there.")
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("profiles", [])


def validate_and_fix_profile(profile: dict[str, Any]) -> dict[str, Any] | None:
    """Validate seed profile and fix age_group if mismatched. Returns None if invalid."""
    required = [
        "name",
        "gender",
        "gender_probability",
        "age",
        "country_id",
        "country_probability",
    ]
    for field in required:
        if field not in profile:
            print(f"Skipping profile missing field '{field}': {profile}")
            return None

    age = int(profile["age"])
    computed_age_group = classify_age_group(age)
    provided_age_group = profile.get("age_group", "").lower()

    if provided_age_group and provided_age_group != computed_age_group:
        print(
            f"Warning: age_group mismatch for '{profile['name']}' "
            f"(provided: {provided_age_group}, computed: {computed_age_group}). "
            f"Using computed value."
        )

    country_id = profile["country_id"].upper()
    country_name = profile.get("country_name", get_country_name(country_id))

    return {
        "id": str(uuid6.uuid7()),
        "name": str(profile["name"]).strip(),
        "gender": str(profile["gender"]).lower(),
        "gender_probability": float(profile["gender_probability"]),
        "age": age,
        "age_group": computed_age_group,
        "country_id": country_id,
        "country_name": country_name,
        "country_probability": float(profile["country_probability"]),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def seed_database() -> None:
    init_db()
    profiles = load_profiles()

    if not profiles:
        print("No profiles found in seed file.")
        return

    conn = get_connection()
    inserted = 0
    skipped = 0

    try:
        for raw in profiles:
            fixed = validate_and_fix_profile(raw)
            if fixed is None:
                skipped += 1
                continue

            if profile_exists_by_name(fixed["name"]):
                skipped += 1
                continue

            conn.execute(
                """
                INSERT INTO profiles (
                    id, name, gender, gender_probability,
                    age, age_group, country_id, country_name, country_probability, created_at
                ) VALUES (
                    :id, :name, :gender, :gender_probability,
                    :age, :age_group, :country_id, :country_name, :country_probability, :created_at
                )
                """,
                fixed,
            )
            inserted += 1

        conn.commit()
    except Exception as exc:
        conn.rollback()
        print(f"Error during seeding: {exc}")
        raise
    finally:
        conn.close()

    print(
        f"Seeding complete: {inserted} inserted, {skipped} skipped (duplicates/invalid)."
    )


if __name__ == "__main__":
    seed_database()
