# FROM gliderlabs/alpine:latest
FROM python:3.4.9-alpine3.8

LABEL maintainer="elastest-users@googlegroups.com"
LABEL description="Executes a simple ESM E2E test"

#RUN mkdir /output
WORKDIR /app
COPY . /app

RUN apk --update add --virtual build-deps python3-dev build-base linux-headers  libffi-dev openssl-dev
RUN apk --update add python3 py3-pip openssl ca-certificates git \
    && pip3 install --upgrade setuptools pip \
    && pip3 install -r /app/requirements.txt

CMD python3 /app/e2e.py
