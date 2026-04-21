from datetime import datetime, timezone
from typing import Any

import uuid6
from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from parser import parse_natural_language
from exceptions import APIException
from models import (
    delete_profile_by_id,
    get_all_profiles,
    get_profile_by_id,
    get_profile_by_name,
    insert_profile,
)
from schemas import (
    NaturalLanguageQuery,
    ProfileCreateRequest,
    ProfileCreateResponse,
    ProfileFullView,
    ProfileListQuery,
    ProfileListResponse,
    ProfileSingleResponse,
)
from services import ExternalAPIError, build_profile_data

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _parse_query_params() -> dict[str, Any]:
    """Extract and validate query parameters for profile listing."""
    try:
        return ProfileListQuery(
            gender=request.args.get("gender"),
            country_id=request.args.get("country_id"),
            age_group=request.args.get("age_group"),
            min_age=request.args.get("min_age", type=int),
            max_age=request.args.get("max_age", type=int),
            min_gender_probability=request.args.get(
                "min_gender_probability", type=float
            ),
            min_country_probability=request.args.get(
                "min_country_probability", type=float
            ),
            sort_by=request.args.get("sort_by", "created_at"),
            order=request.args.get("order", "desc"),
            page=request.args.get("page", 1, type=int),
            limit=request.args.get("limit", 10, type=int),
        ).model_dump()
    except ValidationError:
        raise APIException("Invalid query parameters", 422)


@api_bp.after_request
def apply_cors(response: Response) -> Response:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    return response


@api_bp.route("/profiles", methods=["OPTIONS"])
@api_bp.route("/profiles/<profile_id>", methods=["OPTIONS"])
def handle_options(profile_id: str | None = None):
    return jsonify({}), 200


@api_bp.route("/profiles", methods=["POST"])
def create_profile() -> tuple[Response, int]:
    body = request.get_json(silent=True)

    if not isinstance(body, dict):
        raise APIException("Request body must be a JSON object", 422)

    try:
        req = ProfileCreateRequest.model_validate(body)
    except ValidationError:
        raise APIException("Invalid request body", 422)

    name = req.name

    existing = get_profile_by_name(name)
    if existing:
        return jsonify(
            ProfileCreateResponse(
                data=ProfileFullView.from_db_row(existing),
                message="Profile already exists",
            ).model_dump()
        ), 200

    try:
        external_data = build_profile_data(name)
    except ExternalAPIError:
        raise
    except Exception:
        raise APIException("An unexpected error occurred", 500)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    profile: dict[str, Any] = {
        "id": str(uuid6.uuid7()),
        "name": name,
        "created_at": now,
        **external_data,
    }

    try:
        insert_profile(profile)
    except APIException:
        raise
    except Exception:
        raise APIException("Failed to save profile", 500)

    return jsonify(
        ProfileCreateResponse(data=ProfileFullView.from_db_row(profile)).model_dump(
            exclude_none=True, exclude_unset=True
        )
    ), 201


@api_bp.route("/profiles", methods=["GET"])
def list_profiles() -> tuple[Response, int]:
    params = _parse_query_params()

    try:
        profiles, total = get_all_profiles(
            gender=params.get("gender"),
            country_id=params.get("country_id"),
            age_group=params.get("age_group"),
            min_age=params.get("min_age"),
            max_age=params.get("max_age"),
            min_gender_probability=params.get("min_gender_probability"),
            min_country_probability=params.get("min_country_probability"),
            sort_by=params["sort_by"],
            order=params["order"],
            page=params["page"],
            limit=params["limit"],
        )
    except APIException:
        raise
    except Exception:
        raise APIException("Failed to retrieve profiles", 500)

    return jsonify(
        ProfileListResponse(
            page=params["page"],
            limit=params["limit"],
            total=total,
            data=[ProfileFullView.from_db_row(p) for p in profiles],
        ).model_dump()
    ), 200


@api_bp.route("/profiles/<profile_id>", methods=["GET"])
def get_profile(profile_id: str) -> tuple[Response, int]:
    try:
        profile = get_profile_by_id(profile_id)
    except Exception:
        raise APIException("Failed to retrieve profile", 500)

    if not profile:
        raise APIException("Profile not found", 404)

    return jsonify(
        ProfileSingleResponse(data=ProfileFullView.from_db_row(profile)).model_dump()
    ), 200


@api_bp.route("/profiles/<profile_id>", methods=["DELETE"])
def delete_profile(profile_id: str) -> Response:
    try:
        deleted = delete_profile_by_id(profile_id)
    except Exception:
        raise APIException("Failed to delete profile", 500)

    if not deleted:
        raise APIException("Profile not found", 404)

    return Response(status=204)


@api_bp.route("/profiles/search", methods=["GET"])
def search_profiles() -> tuple[Response, int]:
    """Natural language search endpoint."""
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int) or 1
    limit = request.args.get("limit", 10, type=int) or 10

    if not q:
        raise APIException("Query parameter 'q' is required", 400)

    try:
        nl_query = NaturalLanguageQuery(q=q, page=page, limit=min(limit, 50))
    except ValidationError:
        raise APIException("Invalid query parameters", 422)

    try:
        filters = parse_natural_language(nl_query.q)
    except APIException:
        raise

    try:
        profiles, total = get_all_profiles(
            gender=filters.get("gender"),
            country_id=filters.get("country_id"),
            age_group=filters.get("age_group"),
            min_age=filters.get("min_age"),
            max_age=filters.get("max_age"),
            sort_by="created_at",
            order="desc",
            page=nl_query.page,
            limit=nl_query.limit,
        )
    except Exception:
        raise APIException("Failed to retrieve profiles", 500)

    return jsonify(
        ProfileListResponse(
            page=nl_query.page,
            limit=nl_query.limit,
            total=total,
            data=[ProfileFullView.from_db_row(p) for p in profiles],
        ).model_dump()
    ), 200
