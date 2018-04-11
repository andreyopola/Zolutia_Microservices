#!/usr/bin/env bash
docker build -t gcr.io/copper-oven-193619/zol-payments:test .
gcloud docker -- push gcr.io/copper-oven-193619/zol-payments:test
