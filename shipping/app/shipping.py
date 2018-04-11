import datetime
import os

import pymongo
import requests
from bson import ObjectId
from flask import request, abort, jsonify, Blueprint
from pymongo import MongoClient

bp_shipping = Blueprint('shipping', __name__)

MONGO_HOST = os.environ.get('MONGO_HOST')
mongo_cli = MongoClient(host=MONGO_HOST)
SHIPPING_API_KEY = os.environ.get('SHIPPING_API_KEY')
SELECTED_CARRIER_CODE = 'fedex'


@bp_shipping.route('/shipping/tracking/<int:tracking_number>')
@bp_shipping.route('/order/shipping/status', methods=['POST'])
def fetch_shipping_status(tracking_number=None):
    """Check the status of shipping using order saved in db or external tracking number."""
    if request.json and not tracking_number:  # Order details passed in
        # fetch the tracking number from db records
        args = request.json
        query = {'_id': ObjectId(args['order_id'])}
        order = mongo_cli.db['orders'].find_one(query)
        if order is None:
            abort(404)
        tracking_number = order['tracking_number']
    if tracking_number:
        headers = {
            'api-key': SHIPPING_API_KEY,
            'Content-type': 'application/json'
        }
        payload = {
            'carrier_code': SELECTED_CARRIER_CODE,
            'tracking_number': tracking_number
        }
        r = requests.get('https://api.shipengine.com/v1/tracking',
                         params=payload, headers=headers)
        results = {}
        if r:
            return jsonify(r.json()), 200
        else:
            results['message'] = 'Error, No Response was received'
            return jsonify(results), 204
    else:
        abort(404)
