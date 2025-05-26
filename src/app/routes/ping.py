from flask import Blueprint

ping_bp = Blueprint("ping", __name__, url_prefix="/api/v1")

@ping_bp.route("/ping")
def ping():
    return "pong"