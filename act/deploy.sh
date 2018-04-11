#!/usr/bin/env bash
docker build -t zol-act .
docker rm -f zolutia_act
docker run -d --name zolutia_act --link zolutia_mongodb:mongodb --net zolutiabackend_backend -p 5000:5000 --restart always zol-act



