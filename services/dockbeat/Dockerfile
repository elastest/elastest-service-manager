FROM ingensi/dockbeat
MAINTAINER Ingensi labs <contact@ingensi.com>

COPY dockerbeat.yml /etc/dockbeat/

COPY entrypoint.sh /etc/dockbeat/

RUN ["chmod", "+x", "/etc/dockbeat/entrypoint.sh"]

WORKDIR /etc/dockbeat

ENTRYPOINT ["/etc/dockbeat/entrypoint.sh"]

#CMD [ "-c", "dockerbeat.yml", "-e" ]
