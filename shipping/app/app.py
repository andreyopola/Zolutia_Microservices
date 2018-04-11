from app.shipping import bp_shipping
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(bp_shipping)
    app.config['ERROR_404_HELP'] = False
    return app
