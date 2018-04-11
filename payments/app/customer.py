import os
import string
from hashlib import sha1

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

bp_customer = Blueprint('customer', __name__)


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


@bp_customer.route('/api/v2/customers/new/example')
def create_customer_example():
    """Create a customer instance.

    """
    address = factory.Address(
        City='NY',
        FirstName='James',
        LastName='C'
    )

    customer = factory.CustomerObject(
        BillingAddress=address,
        Currency='USD',
        CustNum='0001',
        Description='a special client',
        Enabled=True,
        Amount=1050.13,
        CustomerID='x1',
        Next='2018-12-31',
        NumLeft=1,
        OrderID='001',
        ReceiptNote='ReceiptNote',
        Schedule='annually',
        SendReceipt=True
    )
    token = build_token()
    response = usaepay_client.service.addCustomer(token, customer)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    else:
        results['message'] = 'New Customer Code created'
        results['customer_code'] = str(response)
        return jsonify(results), 200


@bp_customer.route('/api/v2/customers', methods=['POST'])
def create_customer():
    """Create a customer instance.

    """
    if not request.json:
        abort(400)
    args = request.json
    payment_method = factory.PaymentMethod(
        MethodType='CreditCard',
        MethodName=args['credit_card']['card_name'],  # You can set this as Visa(4)/MC(5)/Amex(3) based on first digit
        CardNumber=args['credit_card']['number'],
        CardExpiration=args['credit_card']['expiry_date'],
        CardCode=args['credit_card']['cvv'],
        AvsStreet=args['address']['street'],
        AvsZip=args['address']['zip'],
        SecondarySort=1
    )
    address = factory.Address(
        City=args['address']['city'],
        Country='US',
        Email=args['address']['email'],
        FirstName=args['address']['firstName'],
        LastName=args['address']['lastName'],
        Phone=args['address']['phone'],
        State=args['address']['state'],
        Street=args['address']['street_1'],
        Street2=args['address']['street_2'],
        Zip=args['address']['zip']
    )

    customer = factory.CustomerObject(
        BillingAddress=address,
        Currency='USD',
        CustNum=args['customer_number'],
        Description=args['description'],
        Enabled=True,
        User=args['user'],
        Amount=args['amount'],
        CustomerID=args['customer_id'],
        OrderID=args['order_id'],
        PaymentMethods=[payment_method],
        Next=args['next'],
        NumLeft=99,
        ReceiptNote='Zolutia Subscription',
        Schedule='quarterly',
        SendReceipt=False
    )
    token = build_token()
    response = usaepay_client.service.addCustomer(token, customer)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    else:
        results['message'] = 'New Customer Code created'
        results['customer_code'] = str(response)
        return jsonify(results), 200


@bp_customer.route('/api/v2/update_credit_card/example')
def updateCreditCard_example():
    token = build_token()
    payMethod = factory.PaymentMethod(
        MethodName='My Visa',
        SecondarySort=1,
        CardNumber='1234567',
        CardExpiration='0919',
        CardCode='PlaceHolder For Now'
    )
    CustNum = "9019481"
    customer = usaepay_client.service.getCustomer(token, CustNum)
    customer.PaymentMethods = payMethod

    response = usaepay_client.updateCustomer(token, CustNum, customer)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    else:
        results['message'] = 'Client Detail (Credit Card) Updated'
        results['customer_code'] = str(response)
        return jsonify(results), 200


@bp_customer.route('/api/v2/credit_cards', methods=['PUT'])
def updateCreditCard():
    if not request.json:
        abort(400)
    args = request.json
    token = build_token()
    payMethod = factory.PaymentMethod(
        MethodName=args['credit_card']['payment_name'],
        SecondarySort=1,
        CardNumber=args['credit_card']['card_number'],
        CardExpiration=(args['credit_card']['credit_card_expiry_month']
                        + args['credit_card']['credit_card_expiry_year']),
        CardCode=args['credit_card']['card_code']
    )
    CustNum = args['customer_number']
    customer = usaepay_client.service.getCustomer(token, CustNum)
    customer.PaymentMethods = payMethod
    response = usaepay_client.updateCustomer(token, CustNum, customer)
    results = {}
    if response is None:
        results['message'] = 'Error, No Response was received'
        return jsonify(results), 204
    else:
        results['message'] = 'Client Detail (Credit Card) Updated'
        results['customer_code'] = str(response)
        return jsonify(results), 200
