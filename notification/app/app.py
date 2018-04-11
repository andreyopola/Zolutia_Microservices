from app.emails import Emails
from app.sms import SMS
from flask import Flask
from flask_cors import CORS
from flask_restful import Api


def create_app():
    app = Flask(__name__)
    CORS(app)

    api = Api(app, prefix='/api/v1')
    api.add_resource(Emails, '/notifications/emails')
    api.add_resource(SMS, '/notifications/sms')
    api.init_app(app)

    app.config['ERROR_404_HELP'] = False

    return app
