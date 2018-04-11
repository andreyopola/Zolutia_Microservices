import os
import time

import requests
import schedule
from pymongo import MongoClient

MONGO_HOST = os.environ.get('MONGO_HOST')
mongo_cli = MongoClient(host=MONGO_HOST)
SHIPPING_HOST = f"http://{os.environ.get('SHIPPING_HOST')}:5000"
ENVIRONMENT = os.environ.get('ENVIRONMENT')


def update_order(order):
    payload = {'order_id': str(order['_id'])}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(f"{SHIPPING_HOST}/order/shipping/status", json=payload, headers=headers)
    status = r.json()['status_description']
    if r.status_code != 200:
        status = 'Tracking Error'
    mongo_cli.db.orders.update_one({'_id': order['_id']}, {'$set': {'tracking_status': status}})


def update_tracking():
    orders = mongo_cli.db.orders.find({
        'tracking_number': {'$exists': True, '$nin': [None, ""]},
        'order_status': {'$nin': ['pending', 'delivered']}})
    for order in orders:
        update_order(order)


def run_scheduler():
    schedule.every(6).hours.do(update_tracking)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
