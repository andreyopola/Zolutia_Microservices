import datetime
import os
from base64 import b64decode
from uuid import uuid4

import bcrypt
from flask import request
from flask_restful import Resource, abort, reqparse
from pymongo import MongoClient

NOTIFICATION_HOST = os.environ.get('NOTIFICATION_HOST')
MONGO_HOST = os.environ.get('MONGO_HOST')


def get_hash(password):
    return bcrypt.hashpw(password, bcrypt.gensalt())


def verify_password(password, password_hash):
    return bcrypt.hashpw(password, password_hash) == password_hash


class Login(Resource):
    def __init__(self):
        super().__init__()

        self._parser = reqparse.RequestParser()
        self._parser.add_argument('Authorization', location='headers',
                                  required=True)

    def get(self):
        args = self._parser.parse_args()
        credentials = args['Authorization'].split()[1]
        login, passwd = b64decode(credentials).decode('UTF-8').split(':')

        mongo_cli = MongoClient(host=MONGO_HOST)
        user = mongo_cli.db.users.find_one({'email_address': login})

        if not user or not verify_password(passwd, user['encrypted_password']):
            abort(403, message='Invalid credentials')

        client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        mongo_cli.db.users.update_one({'_id': user['_id']},
                                      {'$set': {'last_login_ip':
                                                    user.get('current_login_ip'),
                                                'last_login_timestamp': user.get('current_login_timestamp'),
                                                'current_login_ip': client_ip,
                                                'current_login_timestamp': datetime.datetime.utcnow()}})

        return {"role": user['role'], 'user_id': user['_id']}, 200


class Register(Resource):
    def __init__(self):
        super().__init__()

        self._parser_post = reqparse.RequestParser()
        self._parser_post.add_argument('email', dest='email_address', required=True)
        self._parser_post.add_argument('role', required=True)

    def post(self):
        args = self._parser_post.parse_args()
        args['confirmation_status'] = 'Pending'
        token = self._generate_token()
        args['confirmation_token'] = token
        args['confirmation_token_timestamp'] = datetime.datetime.utcnow()
        args['history'] = {'created_on': datetime.datetime.utcnow()}
        args['is_archived'] = False

        mongo_cli = MongoClient(host=MONGO_HOST)

        user = mongo_cli.db.users.find_one({'email_address': args['email_address']})
        if user:
            abort(400, message='Email is already taken')

        user_id = mongo_cli.db.users.insert_one(args).inserted_id

        return {'user_id': user_id, 'token': token}, 200

    def _generate_token(self):
        return str(uuid4())


class ForgotPassword(Resource):
    def __init__(self):
        super().__init__()
        self._parser_get = reqparse.RequestParser()
        self._parser_get.add_argument('email_address', required=True)

        self._parser_post = reqparse.RequestParser()
        self._parser_post.add_argument('email_address', required=True)
        self._parser_post.add_argument('token', required=True)
        self._parser_post.add_argument('password_text', required=True)

    def get(self):
        args = self._parser_get.parse_args()
        mongo_cli = MongoClient(host=MONGO_HOST)
        user = mongo_cli.db.users.find_one(
            {'email_address': args['email_address']})
        if not user:
            abort(400, message='Email not found')
        token = self._generate_token()
        args['forgot_token'] = token
        args['forgot_token_timestamp'] = datetime.datetime.utcnow()
        mongo_cli.db.users.update_one({'_id': user['_id']}, {'$set': args})

        return {'email_address': args['email_address'], 'token': token}, 200

    def post(self):
        args = self._parser_post.parse_args()
        email_address = args['email_address']
        token = args['token']
        password_text = args['password_text']

        mongo_cli = MongoClient(host=MONGO_HOST)
        user = mongo_cli.db.users.find_one({'email_address': email_address})

        if not user:
            abort(400, message='Email not found')
        if not (token or (token[:7] == 'forgot-') or user['forgot_token_timestamp'] > self._token_lifetime()):
            abort(400, message='Invalid token')
        if not password_text:
            abort(400, message='New password not set')
        new_passwd = get_hash(args['password_text'])

        result = mongo_cli.db.users.update_one(
            {'_id': user['_id']},
            {
                '$set': {
                    'reset_password_timestamp': datetime.datetime.utcnow(),
                    'encrypted_password': new_passwd,
                    'history.modified_on': datetime.datetime.utcnow(),
                }
            })
        return {'reset': bool(result.modified_count)}, 200

    def _generate_token(self):
        return str('forgot-') + str(uuid4())

    def _token_lifetime(self):
        return datetime.datetime.utcnow() - datetime.timedelta(7)


class Confirm(Resource):
    def __init__(self):
        super().__init__()

        self._parser_post = reqparse.RequestParser()
        self._parser_post.add_argument('token', required=True)
        self._parser_post.add_argument('password', required=True)

    def post(self):
        args = self._parser_post.parse_args()

        mongo_cli = MongoClient(host=MONGO_HOST)

        result = mongo_cli.db.users.update_one(
            {
                'confirmation_token': args['token'],
                'confirmation_status': 'Pending',
                'confirmation_token_timestamp': {'$gt': self._token_lifetime()}
            },
            {
                '$set': {
                    'confirmation_status': 'Confirmed',
                    'confirmation_timestamp': datetime.datetime.utcnow(),
                    'encrypted_password': get_hash(args['password'])
                }
            })

        response = {'confirmed': bool(result.modified_count)}
        if result.modified_count:
            user = mongo_cli.db.users.find_one(
                {'confirmation_token': args['token']}, projection={'role': True})

            query = {'user_id': user['_id']}
            payload = {'$set': {'status': 'Active'}}

            if user['role'] == 'vet':
                mongo_cli.db.vets.update_one(query, payload)
            elif user['role'] == 'client':
                mongo_cli.db.clients.update_one(query, payload)
            elif user['role'] == 'pharmacy':
                mongo_cli.db.pharmacies.update_one(query, payload)
            elif user['role'] == 'hospital':
                mongo_cli.db.hospitals.update_one(query, payload)

        return response, 200

    def _token_lifetime(self):
        return datetime.datetime.utcnow() - datetime.timedelta(7)


class RegisterSimple(Resource):
    def __init__(self):
        super().__init__()

        self._parser = reqparse.RequestParser()
        self._parser.add_argument('Authorization', location='headers', required=True)
        self._parser.add_argument('role', required=True)

    def post(self):
        args = self._parser.parse_args()
        credentials = args['Authorization'].split()[1]
        login, passwd = b64decode(credentials).decode('UTF-8').split(':')

        mongo_cli = MongoClient(host=MONGO_HOST)

        if mongo_cli.db.users.find_one({'email_address': login}):
            abort(401, message="This login is already registered")

        user_id = mongo_cli.db.users.insert_one({
            'email_address': login,
            'encrypted_password': get_hash(passwd),
            'role': args['role'],
            'confirmation_status': 'Pending',
            'confirmation_token': None,
            'history': {'created_on': datetime.datetime.utcnow()},
            'is_archived': False
        }).inserted_id

        return {'user_id': user_id}, 200


class Reset(Resource):
    def __init__(self):
        super().__init__()

        self._parser_put = reqparse.RequestParser()
        self._parser_put.add_argument('Authorization', location='headers', required=True)
        self._parser_put.add_argument(
            'Zol-New-Password',
            location='headers',
            required=True)

        self._parser_get = reqparse.RequestParser()
        self._parser_get.add_argument('Zol-User-Login', location='headers', required=True)

    def get(self):
        self._parser_get.parse_args()
        # generate confirmation token/link
        # sent an email
        return {}, 200

    def put(self):
        args = self._parser_put.parse_args()
        credentials = args['Authorization'].split()[1]
        login, passwd = b64decode(credentials).decode('UTF-8').split(':')

        mongo_cli = MongoClient(host=MONGO_HOST)
        user = mongo_cli.db.users.find_one({'email_address': login})

        if not user or not verify_password(passwd, user['encrypted_password']):
            abort(403, message='Invalid credentials')

        new_passwd = get_hash(b64decode(args['Zol-New-Password']).decode('UTF8'))

        payload = {
            'encrypted_password': new_passwd,
            'history.modified_on': datetime.datetime.utcnow(),
            'reset_password_time': datetime.datetime.utcnow()
        }

        result = mongo_cli.db.users.update_one({'_id': user['_id']}, {'$set': payload})

        return {"updated": bool(result.modified_count)}, 200
