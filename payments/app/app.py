from app.customer import bp_customer
from app.payment import bp_payment
from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(bp_customer)
    app.register_blueprint(bp_payment)

    app.config['ERROR_404_HELP'] = False

    return app
