from app.act import Client, Patient, Vet
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

    api = Api(app)
    api.add_resource(Client, '/clients')
    api.add_resource(Patient, '/patients')
    api.add_resource(Vet, '/vets')
    api.init_app(app)

    app.config['ERROR_404_HELP'] = False
    app.config['WTF_CSRF_ENABLED'] = False

    return app
