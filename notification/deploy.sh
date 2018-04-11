#!/usr/bin/env bash
docker build -t zol-notifications .
docker rm -f zolutia_notifications
docker run -d --name zolutia_notifications --net zolutiabackend_backend --restart always zol-notifications
