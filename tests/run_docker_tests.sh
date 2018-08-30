#!/usr/bin/env bash

echo '-------------------------------------------------------'
echo 'Testing the core components and their required services'
echo '-------------------------------------------------------'
docker-compose -f docker/docker-compose-tester-core.yml up --build --exit-code-from esm
docker-compose -f docker/docker-compose-tester-core.yml down -v
echo '-------------------------------------------------------'

echo ''
echo '-------------------------------------------------------'
echo 'Testing the Sentinel components and their required services'
echo '-------------------------------------------------------'
docker-compose -f docker/docker-compose-tester-emp.yml up --exit-code-from esm
docker-compose -f docker/docker-compose-tester-emp.yml down -v
echo '-------------------------------------------------------'

echo ''
echo '-------------------------------------------------------'
echo 'Testing the AAA components and their required services'
docker-compose -f docker/docker-compose-tester-aaa.yml up --exit-code-from esm
docker-compose -f docker/docker-compose-tester-aaa.yml down -v
echo '-------------------------------------------------------'

echo ''
echo '-------------------------------------------------------'
echo 'Testing the sql components and their required services'
echo '-------------------------------------------------------'
docker-compose -f docker/docker-compose-tester-sql.yml up --exit-code-from esm
docker-compose -f docker/docker-compose-tester-sql.yml down -v
echo '-------------------------------------------------------'

echo ''
echo '-------------------------------------------------------'
echo 'Running a simple e2e test'
echo '-------------------------------------------------------'
cd e2e
docker-compose -f docker-compose.yml up --build -d
sleep 10s
export USE_EPM=False
python ./e2e.py
docker-compose -f docker-compose.yml down -v
echo '-------------------------------------------------------'
echo ''
