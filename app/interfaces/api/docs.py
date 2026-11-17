"""Rotas de documentação (OpenAPI/Swagger UI) e verificação de saúde."""
from flask import Blueprint, jsonify

from app.interfaces.openapi import construir_openapi

from .support import REGISTRO

bp = Blueprint("docs", __name__)

_SWAGGER_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Oficina Mecânica - Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
  <script>
    window.ui = SwaggerUIBundle({url: "/openapi.json", dom_id: "#swagger-ui", persistAuthorization: true});
  </script>
</body>
</html>
"""


@bp.get("/openapi.json")
def openapi():
    return jsonify(construir_openapi(REGISTRO))


@bp.get("/swagger-ui")
@bp.get("/swagger-ui.html")
def swagger_ui():
    return _SWAGGER_HTML, 200, {"Content-Type": "text/html; charset=utf-8"}


@bp.get("/health")
def health():
    return jsonify({"status": "UP"})
