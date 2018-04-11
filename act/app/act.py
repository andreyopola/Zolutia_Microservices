import datetime
import os

from flask_restful import Resource, abort, reqparse
from pymongo import MongoClient

MONGO_HOST = os.environ.get('MONGO_HOST')
MONGO_PORT = os.environ.get('MONGO_PORT')


class Client(Resource):
    def __init__(self):
        super().__init__()
        self._parser_get = reqparse.RequestParser()
        self._parser_get.add_argument('pims_id', required=True)
        self._parser_get.add_argument('first_name', required=True),
        self._parser_get.add_argument('last_name', required=True)

        self._parser_post = reqparse.RequestParser()
        self._parser_post.add_argument('pims_id', required=True)
        self._parser_post.add_argument('first_name', required=True),
        self._parser_post.add_argument('last_name', required=True),
        self._parser_post.add_argument('gender'),
        self._parser_post.add_argument('email_address'),
        self._parser_post.add_argument('phone'),
        self._parser_post.add_argument('billing_address')
        self._parser_post.add_argument('shipping_address')
        self._parser_post.add_argument('date_of_birth')

        self._parser_put = reqparse.RequestParser()
        self._parser_put.add_argument('client_id', required=True)
        self._parser_put.add_argument('pims_id', required=True)
        self._parser_put.add_argument('first_name', required=True),
        self._parser_put.add_argument('last_name', required=True),
        self._parser_put.add_argument('gender'),
        self._parser_put.add_argument('email_address'),
        self._parser_put.add_argument('phone'),
        self._parser_put.add_argument('billing_address')
        self._parser_put.add_argument('shipping_address')
        self._parser_put.add_argument('date_of_birth')

    def post(self):
        args = self._parser_post.parse_args()
        # Pass in the post args in full to be consumed as they match the collection fields
        payload = args

        mongo_cli = MongoClient(host=MONGO_HOST)

        result = mongo_cli.db.clients.insert(payload)
        new_client = mongo_cli.db.clients.find_one({'pims_id': args['pims_id']})
        if new_client:  # Successfully saved in db
            return {'message': 'client details successfully captured',
                    'client_id': new_client['_id']}, 200
        else:
            return {'message': 'error in capturing client details'}, 400

    def get(self):
        args = self._parser_get.parse_args()
        mongo_cli = MongoClient(host=MONGO_HOST)
        query = {'$and': [{'pims_id': args['pims_id']},
                          {'first_name': args['first_name']},
                          {'last_name': args['last_name']}
                          ]}
        client = mongo_cli.db.clients.find_one(query)
        if not client:
            abort(400, message='Associated client not found')
        return {'client_id': client['_id']}, 200

    def put(self):
        args = self._parser_put.parse_args()
        payload = args
        mongo_cli = MongoClient(host=MONGO_HOST)
        query = {'$and': [{'pims_id': args['pims_id']},
                          {'first_name': args['first_name']},
                          {'last_name': args['last_name']}
                          ]}
        client = mongo_cli.db.clients.find_one(query)
        if not client:
            abort(400, message='Associated client not found')
        result = mongo_cli.db.clients.update_one({'_id': client['_id']},
                                                 {'$set': payload})
        return {'message': 'client details successfully updated',
                'client_id': client['_id']}, 200


class Patient(Resource):
    def __init__(self):
        super().__init__()
        self._parser_get = reqparse.RequestParser()
        self._parser_get.add_argument('pims_id', required=True)
        self._parser_get.add_argument('client_id', required=True)
        self._parser_get.add_argument('name', required=True)

        self._parser_post = reqparse.RequestParser()
        self._parser_post.add_argument('pims_id', required=True)
        self._parser_post.add_argument('client_id', required=True)
        self._parser_post.add_argument('vet_id'),
        self._parser_post.add_argument('hospital_id'),
        self._parser_post.add_argument('name'),
        self._parser_post.add_argument('species'),
        self._parser_post.add_argument('breed')
        self._parser_post.add_argument('birthday')
        self._parser_post.add_argument('age ')
        self._parser_post.add_argument('weight')
        self._parser_post.add_argument('gender')
        self._parser_post.add_argument('is_archived')

        self._parser_put = reqparse.RequestParser()
        self._parser_put.add_argument('pims_id', required=True)
        self._parser_put.add_argument('client_id', required=True)
        self._parser_put.add_argument('vet_id'),
        self._parser_put.add_argument('hospital_id'),
        self._parser_put.add_argument('name', required=True),
        self._parser_put.add_argument('species'),
        self._parser_put.add_argument('color'),
        self._parser_put.add_argument('breed')
        self._parser_put.add_argument('birthday')
        self._parser_put.add_argument('age ')
        self._parser_put.add_argument('weight')
        self._parser_put.add_argument('gender')
        self._parser_put.add_argument('is_archived')

    def post(self):
        args = self._parser_post.parse_args()
        # Pass in the post args in full to be consumed as they match the collection fields
        payload = args
        payload["history"]["created_on"] = datetime.datetime.utcnow()

        mongo_cli = MongoClient(host=MONGO_HOST)

        result = mongo_cli.db.clients.insert(payload)
        query = {'$and': [{'pims_id': args['pims_id']},
                          {'client_id': args['client_id']}]}
        new_patient = mongo_cli.db.patients.find_one(query)

        if new_patient:  # Successfully saved in db
            return {'message': 'patient details successfully captured',
                    'patient_id': new_patient['_id'],
                    'client_id': new_patient['client_id']}, 200
        else:
            return {'message': 'error in capturing patient details'}, 400

    def get(self):
        args = self._parser_get.parse_args()
        mongo_cli = MongoClient(host=MONGO_HOST)
        query = {'$and': [{'pims_id': args['pims_id']},
                          {'client_id': args['client_id']},
                          {'name': args['name']}
                          ]}
        patient = mongo_cli.db.patients.find_one(query)
        if not patient:
            abort(400, message='Associated patient not found')
        return {'patient_id': patient['_id']}, 200

    def put(self):
        args = self._parser_put.parse_args()
        payload = args
        payload["history"]["modified_on"] = datetime.datetime.utcnow()
        mongo_cli = MongoClient(host=MONGO_HOST)
        query = {'$and': [{'pims_id': args['pims_id']},
                          {'client_id': args['client_id']},
                          {'name': args['name']}
                          ]}
        patient = mongo_cli.db.patients.find_one(query)
        if not patient:
            abort(400, message='Associated patient not found')
        result = mongo_cli.db.patients.update_one({'_id': patient['_id']},
                                                  {'$set': payload})
        return {'message': 'patient details successfully updated',
                'patient_id': patient['_id'],
                'client_id': patient['patient_id']}, 200


class Vet(Resource):
    def __init__(self):
        super().__init__()
        self._parser_get = reqparse.RequestParser()
        self._parser_get.add_argument('pims_id', required=True)
        self._parser_get.add_argument('first_name', required=True)
        self._parser_get.add_argument('last_name', required=True)

        self._parser_post = reqparse.RequestParser()
        self._parser_post.add_argument('pims_id', required=True)
        self._parser_post.add_argument('first_name', required=True)
        self._parser_post.add_argument('last_name', required=True)
        self._parser_post.add_argument('gender')
        self._parser_post.add_argument('email_address')
        self._parser_post.add_argument('phone')

        self._parser_put = reqparse.RequestParser()
        self._parser_put.add_argument('pims_id', required=True)
        self._parser_put.add_argument('first_name', required=True)
        self._parser_put.add_argument('last_name', required=True)
        self._parser_put.add_argument('gender')
        self._parser_put.add_argument('email_address')
        self._parser_put.add_argument('phone')

    def post(self):
        args = self._parser_post.parse_args()
        # Pass in the post args in full to be consumed as they match the collection fields
        payload = args

        mongo_cli = MongoClient(host=MONGO_HOST)

        result = mongo_cli.db.vets.insert(payload)
        new_client = mongo_cli.db.clients.find_one({'pims_id': args['pims_id']})
        if new_client:  # Successfully saved in db
            return {'message': 'client details successfully captured',
                    'client_id': new_client['_id']}, 200
        else:
            return {'message': 'error in capturing client details'}, 400

    def get(self):
        args = self._parser_get.parse_args()
        mongo_cli = MongoClient(host=MONGO_HOST)
        query = {'$and': [{'pims_id': args['pims_id']},
                          {'first_name': args['first_name']},
                          {'last_name': args['last_name']}
                          ]}
        vet = mongo_cli.db.vets.find_one(query)
        if not vet:
            abort(400, message='Associated client not found')
        return {'vet_id': vet['_id'], 'hospital_id': vet['hospital_id']}, 200

    def put(self):
        args = self._parser_put.parse_args()
        payload = args
        mongo_cli = MongoClient(host=MONGO_HOST)
        query = {'$and': [{'pims_id': args['pims_id']},
                          {'first_name': args['first_name']},
                          {'last_name': args['last_name']}
                          ]}
        client = mongo_cli.db.clients.find_one(query)
        if not client:
            abort(400, message='Associated client not found')
        result = mongo_cli.db.clients.update_one({'_id': client['_id']},
                                                 {'$set': payload})
        return {'message': 'client details successfully updated',
                'client_id': client['_id']}, 200

