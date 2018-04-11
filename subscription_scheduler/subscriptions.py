import datetime
import os
import time

import requests
import schedule
from pymongo import MongoClient

MONGO_HOST = os.environ.get('MONGO_HOST')
mongo_cli = MongoClient(host=MONGO_HOST)
NOTIFICATION_HOST = os.environ.get('NOTIFICATION_HOST')
PAYMENT_HOST = os.environ.get('PAYMENT_HOST')
FAIL_PAYMENT_CLIENT_TEMPLATE = os.environ.get('FAIL_PAYMENT_CLIENT_TEMPLATE')
ORDER_PHARMACY_TEMPLATE = os.environ.get('ORDER_PHARMACY_TEMPLATE')
ORDER_CLIENT_TEMPLATE = os.environ.get('ORDER_PHARMACY_TEMPLATE')


def create_order(subscription):
    last_order = mongo_cli.db.orders.find_one({'subscription_id': subscription['_id']},
                                              sort=[('order_number', -1)])
    new_order = last_order

    new_order.pop('_id')
    new_order['history'] = {'created_on': datetime.datetime.utcnow()}
    new_order['order_number'] = mongo_cli.db.orders.find_one({},
                                                             sort=[('order_number', -1)])['order_number']
    new_order['shipping_date'] = datetime.datetime.utcnow() + datetime.timedelta(days=4)
    new_order['delivery_date'] = None

    box_no = subscription['future_boxes'][0]['box_no']
    current_box = None
    for box in subscription['boxes']:
        if box['box_no'] == box_no:
            current_box = box
            break

    subtotal = 0.0
    for p in current_box['items']:
        pipeline = [  # wtf i've done
            {'$match': {'_id': new_order['hospital_id']}},
            {'$unwind': '$formulary'},
            {'$match': {'formulary.product_id': p['product_id']}},
            {'$unwind': '$formulary.available_options'},
            {'$match': {'formulary.available_options.strength': p.get('strength', p.get('size'))}}
        ]
        product = list(mongo_cli.db.hospitals.aggregate(pipeline))[0]
        p['product_price'] = product['formulary']['available_options']['price']

        subtotal += float(p['product_price']) * int(p['quantity'])
    total = subtotal + float(last_order['tax']) + float(last_order['shipping_amount'])
    new_order['subtotal_price'] = str(round(subtotal, 2))
    new_order['total_price'] = str(round(total, 2))

    new_order['order_contents'] = current_box['items']
    new_order['box_no'] = box_no

    product_types = set()
    for p in new_order['order_contents']:
        product = mongo_cli.db.products.find_one({'_id': p['product_id']})
        product_types.add(product['type'].lower())

    if {'otc'} == product_types:
        new_order['pharmacy_type'] = 'OTC'
    elif '502b' in product_types:
        new_order['pharmacy_type'] = '502b'
    elif 'compounded' in product_types:
        new_order['pharmacy_type'] = 'Compounded'
    else:
        new_order['pharmacy_type'] = 'Retail'

    order_id = mongo_cli.db.orders.insert_one(new_order).inserted_id

    notify_pharmacy_order(new_order['pharmacy_id'], new_order['order_number'])
    notify_client_order(new_order['client_id'], new_order['order_number'])

    past_box = subscription['future_boxes'][0]
    past_box['order_id'] = order_id
    future_box = subscription['future_boxes'][-1]
    future_box['shipping_date'] += datetime.timedelta(days=90)

    mongo_cli.db.subscriptions.update_one({'_id': subscription['_id']}, {'$pop': {'future_boxes': -1}})
    mongo_cli.db.subscriptions.update_one(
        {'_id': subscription['_id']}, {'$push': {'future_boxes': future_box, 'past_boxes': past_box}})

    return order_id


def notify_pharmacy_order(pharmacy_id, order_number):
    pharmacy = mongo_cli.db.pharmacies.find_one({'_id': pharmacy_id})

    body = {
        'from_email': 'noreply@zolutia.com',
        'from_name': 'Zolutia',
        'to_email': pharmacy['email'],
        'to_name': pharmacy['name'],
        'subject': 'New order in Zolutia',
        'template_id': ORDER_PHARMACY_TEMPLATE,
        'substitutions': {
            '{name}': pharmacy['name'],
            '{order_number}': str(order_number),
        }
    }
    url = f'http://{NOTIFICATION_HOST}:5000/api/v1/notifications/emails'
    email_resp = requests.post(url, json=body)

    sms_text = f"Dear {pharmacy['name']}, you have a new order №{order_number} " \
               f"in Zolutia. For more details, log in."
    payload = {
        'to': pharmacy['phone'],
        'message': sms_text
    }
    url = f'http://{NOTIFICATION_HOST}:5000/api/v1/notifications/sms'
    sms_resp = requests.post(url, json=payload)

    resp = {
        'email': 'sent' if email_resp.status_code == 200 else email_resp.json(),
        'sms': 'sent' if sms_resp.status_code == 200 else sms_resp.json(),
    }

    return resp, 200


def notify_client_order(client_id, order_number):
    client = mongo_cli.db.clients.find_one({'_id': client_id})

    body = {
        'from_email': 'sales@zolutia.com',
        'from_name': 'Zolutia',
        'to_email': client['email_address'],
        'to_name': f"{client['first_name']} {client['last_name']}",
        'subject': 'Order confirmation',
        'template_id': ORDER_CLIENT_TEMPLATE,
        'substitutions': {
            '{name}': f"{client['first_name']} {client['last_name']}",
            '{order}': str(order_number)
        }
    }
    url = f'http://{NOTIFICATION_HOST}:5000/api/v1/notifications/emails'
    email_resp = requests.post(url, json=body)
    client_name = f"{client['first_name']} {client['last_name']}"

    sms_text = f"Dear {client_name}, you have a new order №{order_number} in Zolutia. For more details, log in."
    payload = {
        'to': client['phone']['cell'],
        'message': sms_text
    }
    url = f'http://{NOTIFICATION_HOST}:5000/api/v1/notifications/sms'
    sms_resp = requests.post(url, json=payload)

    resp = {
        'email': 'sent' if email_resp.status_code == 200 else email_resp.json(),
        'sms': 'sent' if sms_resp.status_code == 200 else sms_resp.json(),
    }

    return resp, 200


def make_quicksale(order_id):
    payload = {'order_id': order_id}
    headers = {'Content-Type': 'application/json'}
    r = requests.post(f"{PAYMENT_HOST}/api/v2/quicksales", params=payload, headers=headers)
    if r.status_code == 200:
        mongo_cli.db.orders.update_one({'_id': order_id}, {'$set': {'order_status': 'processing'}})
    else:
        order = mongo_cli.db.orders.findOne({'_id': order_id})
        notify_client_payment_failed(order['client_id'], order['order_number'])


def notify_client_payment_failed(client_id, order_number):
    client = mongo_cli.db.clients.find_one({'_id': client_id})

    body = {
        'from_email': 'sales@zolutia.com',
        'from_name': 'Zolutia',
        'to_email': client['email_address'],
        'to_name': f"{client['first_name']} {client['last_name']}",
        'subject': 'Order confirmation',
        'template_id': FAIL_PAYMENT_CLIENT_TEMPLATE,
    }
    url = f'http://{NOTIFICATION_HOST}:5000/api/v1/notifications/emails'
    email_resp = requests.post(url, json=body)

    sms_text = 'There was an issue with your payment. Please visit us at www.Zolutia.com ' \
               'to update or give us a call at 888-xxx-xxxx.'
    sms_payload = {
        'to': client['phone']['cell'],
        'message': sms_text
    }
    url = f'http://{NOTIFICATION_HOST}:5000/api/v1/notifications/sms'
    sms_resp = requests.post(url, json=sms_payload)

    resp = {
        'email': 'sent' if email_resp.status_code == 200 else email_resp.json(),
        'sms': 'sent' if sms_resp.status_code == 200 else sms_resp.json(),
    }

    return resp, 200


def process_payments():
    today = datetime.date.today()
    today = datetime.datetime(today.year, today.month, today.day)
    subs = mongo_cli.db.subscriptions.find({'subscription_status': 'Active',
                                            'upcoming_shipment_date': {'$gte': today,
                                                                       '$lt': today + datetime.timedelta(days=1)}})
    for sub in subs:
        order_id = create_order(sub)
        make_quicksale(order_id)


def run_scheduler():
    schedule.every().day.at("08:00").do(process_payments)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
