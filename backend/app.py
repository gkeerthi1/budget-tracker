"""Budget Tracker - Flask application entry point."""
from flask import Flask, jsonify

from models import init_db
from routes.auth import auth_bp
from routes.categories import categories_bp
from routes.transactions import transactions_bp
from routes.dashboard import dashboard_bp
from routes.recurring import recurring_bp
from routes.goals import goals_bp


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-change-me"
    app.config["DATABASE"] = "budget_tracker.db"

    if config:
        app.config.update(config)

    init_db(app.config["DATABASE"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(recurring_bp)
    app.register_blueprint(goals_bp)

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "service": "budget-tracker"})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
