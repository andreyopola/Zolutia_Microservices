FROM python:3.6-jessie

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV MONGO_HOST=mongodb
ENV MONGO_PORT=27017
ENV USAEPAY_KEY=_X48qB58Yv4rpz9s9XFKA2O12h20HxR5
ENV USAEPAY_PIN=97315
ENV USAEPAY_WSDL='https://sandbox.usaepay.com/soap/gate/6VCZS4FF/usaepay.wsdl'

EXPOSE 5000

CMD ["python" ,"manage.py" ,"runserver"]
