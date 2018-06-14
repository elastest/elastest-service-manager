#!/usr/bin/env bash

# test the core components and their required services
docker-compose -f docker/docker-compose-tester-core.yml up --build --exit-code-from esm
docker-compose -f docker/docker-compose-tester-core.yml down -v

# test the Sentinel components and their required services
docker-compose -f docker/docker-compose-tester-emp.yml up --exit-code-from esm
docker-compose -f docker/docker-compose-tester-emp.yml down -v

# test the AAA components and their required services
docker-compose -f docker/docker-compose-tester-aaa.yml up --exit-code-from esm
docker-compose -f docker/docker-compose-tester-aaa.yml down -v

# test the sql components and their required services
docker-compose -f docker/docker-compose-tester-sql.yml up --exit-code-from esm
docker-compose -f docker/docker-compose-tester-sql.yml down -v