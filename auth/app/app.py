from app.auth import Login, Register, Reset, Confirm, ForgotPassword
from app.json import MongoEncoder
from flask import Flask
from flask_cors import CORS
from flask_restful import Api


def create_app():
    app = Flask(__name__)
    app.config['RESTFUL_JSON'] = {
        'separators': (', ', ': '),
        'indent': 2,
        'cls': MongoEncoder
    }
    CORS(app)

    api = Api(app, prefix='/api/v1/auth')
    api.add_resource(Login, '/login')
    api.add_resource(Register, '/register')
    api.add_resource(Confirm, '/confirm')
    api.add_resource(Reset, '/reset')
    api.add_resource(ForgotPassword, '/forgotpassword')
    api.init_app(app)

    app.config['ERROR_404_HELP'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    return app
