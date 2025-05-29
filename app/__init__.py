from flask import Flask, jsonify
from flask_restx import Api
from app.config import load_configurations, configure_logging
from routes.routes import webhook_blueprint, health_blueprint

def create_app():
    app = Flask(__name__)

    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()

    # Register any Flask blueprints
    app.register_blueprint(health_blueprint)
    app.register_blueprint(webhook_blueprint)

    # ✅ Setup RESTx for Swagger
    api = Api(
        app,
        version="1.0",
        title="WhatsApp API",
        description="API to send WhatsApp messages",
        doc="/swagger"
    )

    return app
