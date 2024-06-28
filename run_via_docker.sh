#!/usr/bin/env bash

docker build -t broad-atlas:latest .
docker run --rm -p 5001:5001 broad-atlas:latest