FROM gliderlabs/alpine:latest

LABEL maintainer="elastest-users@googlegroups.com"
LABEL description="Executes a simple ESM E2E test"

#RUN mkdir /output
WORKDIR /app
COPY . /app

RUN apk --update add --virtual build-deps python3-dev build-base linux-headers
RUN apk --update add python3 py3-pip openssl ca-certificates git \
    && pip3 install --upgrade setuptools pip \
    && pip3 install -r /app/requirements.txt

CMD /usr/bin/python3 /app/e2e.py
