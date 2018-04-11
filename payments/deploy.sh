#!/usr/bin/env bash
docker build -t zol-payments .
docker rm -f zolutia_payments
docker run -d --name zolutia_payments --link zolutia_mongodb:mongodb --net zolutiabackend_backend --restart always zol-payments
