import os

from flask_restful import Resource, abort, reqparse
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

TWILIO_ACCOUNT = os.environ.get('TWILIO_ACCOUNT')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
ZOLUTIA_PHONE = os.environ.get('ZOLUTIA_PHONE')


class SMS(Resource):
    def __init__(self):
        super().__init__()

        self._parser = reqparse.RequestParser()
        self._parser.add_argument('to', required='True')
        self._parser.add_argument('message', required='True')

    def post(self):
        args = self._parser.parse_args()

        twilio_cli = Client(TWILIO_ACCOUNT, TWILIO_TOKEN)
        try:
            message = twilio_cli.messages.create(to=args['to'],
                                                 from_=ZOLUTIA_PHONE,
                                                 body=args['message'])
        except TwilioRestException as e:
            abort(400, message=e.msg)

        return {"sent": True}, 200
