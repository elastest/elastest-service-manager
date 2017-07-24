FROM gliderlabs/alpine:latest

LABEL maintainer "elastest-users@googlegroups.com"
LABEL version="0.1.0"
LABEL description="Builds the service manager docker image."

WORKDIR ../
RUN pwd
COPY . /app/

#RUN apk --update add python3 py3-pip openssl ca-certificates \
#    && pip3 install -r /app/requirements.txt

# endpoint of the EPM
# ENV EPM_SVC_EP http://somewhere.io:4533/epm

# port on which the ESM runs
ENV ESM_PORT 8080

EXPOSE 8080

#CMD ["/usr/bin/python3", "/app/runesm.py"]
# launch container
ENTRYPOINT ["/bin/sh"]
