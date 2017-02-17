#!/bin/bash

rm -rf db*
docker rm -f `docker ps -q`
