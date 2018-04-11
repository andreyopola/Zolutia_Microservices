#!/usr/bin/env bash
docker build -t zol-scheduler1 .
docker rm -f zolutia_scheduler1
docker run -d --name zolutia_scheduler1 --link zolutia_mongodb:mongodb --link zolutia_notifications:notification --net zolutiabackend_backend --restart always zol-scheduler1
