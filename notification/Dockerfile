FROM python:3.6-jessie

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV MONGO_HOST=mongodb
ENV MONGO_PORT=27017
ENV SENDGRID_API_KEY=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
ENV TWILIO_ACCOUNT=ACeedaf4ece19bfeb327b3cdb7c5357851
ENV TWILIO_TOKEN=4b11029c5b6f7117cfbcb17928d8c010
ENV ZOLUTIA_PHONE="+12107672375"

EXPOSE 5000

CMD ["python", "manage.py", "runserver"]
