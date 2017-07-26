#!/bin/sh
cd /etc/dockbeat
sed -i 's/LOGSTASH_HOST/'"$LOGSTASH_HOST"'/g' dockerbeat.yml
dockbeat -c dockerbeat.yml -e -v
