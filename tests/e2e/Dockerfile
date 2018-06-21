FROM gliderlabs/alpine:latest

LABEL maintainer="elastest-users@googlegroups.com"
LABEL description="Builds the test service manager docker image."

RUN mkdir /output
WORKDIR /app
COPY . /app

RUN apk --update add --virtual build-deps python3-dev build-base linux-headers
RUN apk --update add python3 py3-pip openssl ca-certificates git \
    && pip3 install --upgrade setuptools pip tox \
    && pip3 install -r /app/src/requirements.txt

ENV ESM_PORT 8080
ENV ESM_CHECK_PORT 5000

EXPOSE 8080 5000

CMD tox -c /app/tests/docker/tox.ini
