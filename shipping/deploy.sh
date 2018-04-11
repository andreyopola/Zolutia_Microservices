#!/usr/bin/env bash
docker build -t zol-shipping .
docker rm -f zolutia_shipping
docker run -d --name zolutia_shipping --link zolutia_mongodb:mongodb --net zolutiabackend_backend --restart always zol-shipping
