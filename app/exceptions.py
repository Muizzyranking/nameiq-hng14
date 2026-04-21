from flask import jsonify, Response
from typing import Any


class APIException(Exception):
    """Custom exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
    ) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def register_error_handlers(app) -> None:
    """Register global exception handlers on the Flask app."""

    @app.errorhandler(APIException)
    def handle_api_exception(exc: APIException) -> tuple[Response, int]:
        return jsonify({"status": "error", "message": exc.message}), exc.status_code

    @app.errorhandler(404)
    def handle_not_found(_: Any) -> tuple[Response, int]:
        return jsonify({"status": "error", "message": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_: Any) -> tuple[Response, int]:
        return (
            jsonify({"status": "error", "message": "Method not allowed"}),
            405,
        )

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception) -> tuple[Response, int]:
        return (
            jsonify({"status": "error", "message": "An unexpected error occurred"}),
            500,
        )
