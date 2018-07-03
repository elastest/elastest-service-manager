#!/usr/bin/env bash
set -x

docker-compose -f ./docker-compose.yml up -d
export ESM_IP=`docker inspect --format="{{.NetworkSettings.Networks.e2e_elastest_elastest.IPAddress}}" esm`
docker build -t dizz/esm_e2e:latest .
sleep 20
docker run -t --name esm_e2e --network e2e_elastest_elastest -e ESM_EP_IP=${ESM_IP} dizz/esm_e2e:latest

docker-compose -f ./docker-compose.yml down -v
docker rm -f esm_e2e
