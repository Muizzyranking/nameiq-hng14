from datetime import datetime, timezone
from typing import Any

import uuid6
from flask import Flask, Response, jsonify, request

from models import (
    delete_profile_by_id,
    get_all_profiles,
    get_profile_by_id,
    get_profile_by_name,
    init_db,
    insert_profile,
)
from services import ExternalAPIError, build_profile_data

app = Flask(__name__)


@app.after_request
def apply_cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return response


@app.route("/api/profiles", methods=["OPTIONS"])
@app.route("/api/profiles/<profile_id>", methods=["OPTIONS"])
def handle_options(profile_id: str | None = None):
    return jsonify({}), 200


def error_response(message: str, status: int) -> tuple[Response, int]:
    return jsonify({"status": "error", "message": message}), status


def full_profile_view(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": profile["id"],
        "name": profile["name"],
        "gender": profile["gender"],
        "gender_probability": round(profile["gender_probability"], 2),
        "sample_size": profile["sample_size"],
        "age": profile["age"],
        "age_group": profile["age_group"],
        "country_id": profile["country_id"],
        "country_probability": round(profile["country_probability"], 2),
        "created_at": profile["created_at"],
    }


def list_profile_view(profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": profile["id"],
        "name": profile["name"],
        "gender": profile["gender"],
        "age": profile["age"],
        "age_group": profile["age_group"],
        "country_id": profile["country_id"],
    }


@app.route("/api/profiles", methods=["POST"])
def create_profile() -> tuple[Response, int]:
    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        return error_response("Request body must be a JSON object", 422)

    name = body.get("name")

    if name is None or (isinstance(name, str) and name.strip() == ""):
        return error_response("name is required and cannot be empty", 400)

    if not isinstance(name, str):
        return error_response("name must be a string", 422)

    name = name.strip()

    existing = get_profile_by_name(name)
    if existing:
        return jsonify(
            {
                "status": "success",
                "message": "Profile already exists",
                "data": full_profile_view(existing),
            }
        ), 200

    try:
        external_data = build_profile_data(name)
    except ExternalAPIError as exc:
        return error_response(str(exc), 502)
    except Exception:
        return error_response("An unexpected error occurred", 500)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    profile: dict[str, Any] = {
        "id": str(uuid6.uuid7()),
        "name": name,
        "created_at": now,
        **external_data,
    }

    try:
        insert_profile(profile)
    except Exception:
        return error_response("Failed to save profile", 500)

    return jsonify({"status": "success", "data": full_profile_view(profile)}), 201


@app.route("/api/profiles", methods=["GET"])
def list_profiles() -> tuple[Response, int]:
    gender = request.args.get("gender")
    country_id = request.args.get("country_id")
    age_group = request.args.get("age_group")

    try:
        profiles = get_all_profiles(
            gender=gender,
            country_id=country_id,
            age_group=age_group,
        )
    except Exception:
        return error_response("Failed to retrieve profiles", 500)

    return jsonify(
        {
            "status": "success",
            "count": len(profiles),
            "data": [list_profile_view(p) for p in profiles],
        }
    ), 200


@app.route("/api/profiles/<profile_id>", methods=["GET"])
def get_profile(profile_id: str) -> tuple[Response, int]:
    try:
        profile = get_profile_by_id(profile_id)
    except Exception:
        return error_response("Failed to retrieve profile", 500)

    if not profile:
        return error_response("Profile not found", 404)

    return jsonify({"status": "success", "data": full_profile_view(profile)}), 200


@app.route("/api/profiles/<profile_id>", methods=["DELETE"])
def delete_profile(profile_id: str):
    try:
        deleted = delete_profile_by_id(profile_id)
    except Exception:
        return error_response("Failed to delete profile", 500)

    if not deleted:
        return error_response("Profile not found", 404)

    return Response(status=204)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
