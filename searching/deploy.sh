#!/usr/bin/env bash
docker build -t zol-search .
docker rm -f zolutia_search
docker run -d --name zolutia_search --link zolutia_mongodb:mongodb --net zolutiabackend_backend --restart always zol-search
