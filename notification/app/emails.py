import os
import urllib

from flask_restful import Resource, abort, reqparse
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import *

SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')


class Emails(Resource):
    def __init__(self):
        super().__init__()

        self._parser = reqparse.RequestParser()
        self._parser.add_argument('from_email', required='True')
        self._parser.add_argument('from_name', required='True')
        self._parser.add_argument('to_email', required='True')
        self._parser.add_argument('to_name', required='True')
        self._parser.add_argument('subject', required='True')
        self._parser.add_argument('template_id', required='True')
        self._parser.add_argument('substitutions', type=dict)

    def post(self):
        args = self._parser.parse_args()

        sg_cli = SendGridAPIClient(apikey=SENDGRID_API_KEY)
        payload = self._build_mail(args)
        try:
            response = sg_cli.client.mail.send.post(request_body=payload)
        except urllib.error.HTTPError as e:
            abort(e.code, message=e.reason)
        return {"sent": True}, 200

    def _build_mail(self, args):
        email = Mail()

        email.from_email = Email(args['from_email'], args['from_name'])
        email.template_id = args['template_id']

        personalization = Personalization()
        personalization.add_to(Email(args['to_email'], args['to_name']))
        personalization.subject = args['subject']
        if args.get('substitutions'):
            for template, value in args['substitutions'].items():
                personalization.add_substitution(Substitution(template, value))

        email.add_personalization(personalization)

        return email.get()
