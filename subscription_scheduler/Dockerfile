FROM python:3.6-jessie

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV MONGO_HOST=mongodb
ENV MONGO_PORT=27017
ENV NOTIFICATION_HOST=notification
ENV ORDER_PHARMACY_TEMPLATE=694fd8af-101e-47bd-91b1-93b72187055e
ENV ORDER_CLIENT_TEMPLATE=4b9e4ce8-cfc6-4255-bb5d-c2ffa10c6a52
ENV FAIL_PAYMENT_CLIENT_TEMPLATE=8d2e1201-cbc6-4d6e-981f-40b61114e7fe

CMD ["python" ,"subscriptions.py"]
