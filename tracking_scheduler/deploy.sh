#!/usr/bin/env bash
docker build -t zol-scheduler2 .
docker rm -f zolutia_scheduler2
docker run -d --name zolutia_scheduler2 --link zolutia_mongodb:mongodb --link zolutia_shipping:shipping --net zolutiabackend_backend --restart always zol-scheduler2
