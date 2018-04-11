import os
import string
from hashlib import sha1

from bson import ObjectId
from flask import request, abort, jsonify, Blueprint
from pymongo import MongoClient
from zeep import Client

MONGO_HOST = os.environ.get('MONGO_HOST')
USAEPAY_KEY = os.environ.get('USAEPAY_KEY')
USAEPAY_PIN = os.environ.get('USAEPAY_PIN')
USAEPAY_WSDL = os.environ.get('USAEPAY_WSDL')

usaepay_client = Client(USAEPAY_WSDL)
factory = usaepay_client.type_factory('ns0')
mongo_cli = MongoClient(host=MONGO_HOST)

bp_payment = Blueprint('payment', __name__)


def build_token():
    """Create the request token."""
    client_ip = '74.71.168.169'
    seed = string.ascii_lowercase
    apikey = USAEPAY_KEY
    apipin = USAEPAY_PIN
    prehash = (apikey + seed + apipin).encode('utf-8')
    pinhash = str(sha1(prehash).hexdigest())
    euhash = factory.ueHash(HashValue=pinhash, Seed=seed, Type='sha1')
    token = factory.ueSecurityToken(ClientIP=client_ip, PinHash=euhash, SourceKey=apikey)
    return token


@bp_payment.route('/api/v2/example_trans_run')
def example_run_transaction():
    credit_card_details = factory.CreditCardData(
        CardNumber='123456789',
        CardExpiration='0919',
        CardCode='PlaceHolder For Now',  # Will this field be present in the incoming request data?
        CAVV='123',
        AvsZip='A zip code',
        AvsStreet='My Street'
    )
    transaction_details = factory.TransactionDetail(
        Description='Product Description',
        Amount=1000,
        Invoice='Invoice Details'
    )
    req_data = factory.TransactionRequestObject(
        AccountHolder='Account Holder Name',  # Confirm if this field will be needed
        Details=transaction_details,
        CreditCardData=credit_card_details
    )
    token = build_token()
    response = usaepay_client.service.runTransaction(token, req_data)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    if response.ResultCode == "A":
        results['message'] = 'Transaction Approved'
        results['reference_number'] = str(response.RefNum)
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 200
    if response.ResultCode == "D":
        results['message'] = ('Transaction Declined, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400
    else:
        results['message'] = ('Transaction Error, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400


@bp_payment.route('/api/v2/transactions', methods=['POST'])
def run_transaction():
    """Run a transaction using the order id.

    """
    if not request.json:
        abort(400)
    args = request.json
    query = {'_id': ObjectId(args['order_id'])}
    order = mongo_cli.db['orders'].find_one(query)
    if order is None:
        abort(404)
    client = mongo_cli.db['clients'].find_one({'_id': order['client_id']})

    credit_card_details = factory.CreditCardData(
        CardNumber=args['credit_card_number'],
        CardExpiration=args['credit_card_expiry_month'] + args['credit_card_expiry_year'],
        CardCode=args['credit_card_cvv'],
        AvsZip=order['shipping_address']['zip'],
        AvsStreet=order['shipping_address']['street_1'] + ' ' + order['shipping_address']['street_2']
    )
    transaction_details = factory.TransactionDetail(
        Description=order['type'],
        Amount=order['total_price'],
        Invoice=order['order_number']
    )
    req_data = factory.TransactionRequestObject(
        AccountHolder=f"{client['first_name']} {client['last_name']}",
        Details=transaction_details,
        CreditCardData=credit_card_details
    )
    token = build_token()
    response = usaepay_client.service.runTransaction(token, req_data)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    if response.ResultCode == "A":
        results['message'] = 'Transaction Approved'
        results['reference_number'] = str(response.RefNum)
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 200
    if response.ResultCode == "D":
        results['message'] = ('Transaction Declined, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400
    else:
        results['message'] = ('Transaction Error, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400


@bp_payment.route('/api/v2/quicksale/example')
def example_quick_sale():
    details = factory.TransactionDetail(
        Amount="34.50",
        Description="Example QuickSale",
        Invoice="123456"
    )
    refnum = "46990567"
    authonly = False
    token = build_token()
    response = usaepay_client.service.runQuickSale(token, refnum, details, authonly)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    if response.ResultCode == "A":
        results['message'] = 'Transaction Approved'
        results['reference_number'] = str(response.RefNum)
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 200
    if response.ResultCode == "D":
        results['message'] = ('Transaction Declined, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400
    else:
        results['message'] = ('Transaction Error, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400


@bp_payment.route('/api/v2/quicksales', methods=['POST'])
def quicksale():
    """Run a quick sale using the order id.
    """
    if not request.json:
        abort(400)
    args = request.json
    query = {'_id': ObjectId(args['order_id'])}
    order = mongo_cli.db['orders'].find_one(query)
    if order is None:
        abort(404)

    details = factory.TransactionDetail(
        Amount=order['total_price'],
        Description=order['type'],
        Invoice=order['order_number']
    )
    refnum = order['order_number']
    authonly = False
    token = build_token()
    response = usaepay_client.service.runQuickSale(token, refnum, details, authonly)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    if response.ResultCode == "A":
        results['message'] = 'Transaction Approved'
        results['reference_number'] = str(response.RefNum)
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 200
    if response.ResultCode == "D":
        results['message'] = ('Transaction Declined, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400
    else:
        results['message'] = ('Transaction Error, Reason: {}'
            .format(response.Error))
        results['result_code'] = str(response.ResultCode)
        return jsonify(results), 400
