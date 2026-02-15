import sys
import os

# Add repo root to path so `src` package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask
from flask_cors import CORS

from .routes.grammar import grammar_bp
from .routes.parser import parser_bp


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(grammar_bp)
    app.register_blueprint(parser_bp)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
