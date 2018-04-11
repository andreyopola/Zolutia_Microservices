#!/usr/bin/env bash
docker build -t zol-auth .
docker rm -f zolutia_auth 
docker run -d --name zolutia_auth --link zolutia_mongodb:mongodb --net zolutiabackend_backend --restart always zol-auth
