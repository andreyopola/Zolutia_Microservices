FROM python:3.6-jessie

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV MONGO_HOST=mongodb
ENV MONGO_PORT=27017
EXPOSE 5000

CMD ["python" ,"manage.py" ,"runserver"]
