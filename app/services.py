import requests
from typing import Any

GENDERIZE_URL = "https://api.genderize.io"
AGIFY_URL = "https://api.agify.io"
NATIONALIZE_URL = "https://api.nationalize.io"

TIMEOUT_SEC = 10


class ExternalAPIError(Exception):
    def __init__(self, api_name: str) -> None:
        self.api_name = api_name
        super().__init__(f"{api_name} returned an invalid response")


def classify_age_group(age: int) -> str:
    if age <= 12:
        return "child"
    elif age <= 19:
        return "teenager"
    elif age <= 59:
        return "adult"
    else:
        return "senior"


def fetch_gender(name: str) -> dict[str, Any]:
    try:
        response = requests.get(
            GENDERIZE_URL, params={"name": name}, timeout=TIMEOUT_SEC
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except Exception:
        raise ExternalAPIError("Genderize")

    gender = data.get("gender")
    count = data.get("count")

    if not gender or not count:
        raise ExternalAPIError("Genderize")

    return {
        "gender": gender,
        "gender_probability": round(data.get("probability", 0.0), 2),
        "sample_size": count,
    }


def fetch_age(name: str) -> dict[str, Any]:
    try:
        response = requests.get(AGIFY_URL, params={"name": name}, timeout=TIMEOUT_SEC)
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except Exception:
        raise ExternalAPIError("Agify")

    age = data.get("age")

    if age is None:
        raise ExternalAPIError("Agify")

    return {
        "age": age,
        "age_group": classify_age_group(age),
    }


def fetch_nationality(name: str) -> dict[str, Any]:
    try:
        response = requests.get(
            NATIONALIZE_URL, params={"name": name}, timeout=TIMEOUT_SEC
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
    except Exception:
        raise ExternalAPIError("Nationalize")

    countries: list[dict[str, Any]] = data.get("country") or []

    if not countries:
        raise ExternalAPIError("Nationalize")

    top = max(countries, key=lambda c: c.get("probability", 0.0))

    return {
        "country_id": top.get("country_id", ""),
        "country_probability": round(top.get("probability", 0.0), 2),
    }


def build_profile_data(name: str) -> dict[str, Any]:
    gender_data = fetch_gender(name)
    age_data = fetch_age(name)
    nationality_data = fetch_nationality(name)

    return {**gender_data, **age_data, **nationality_data}
