# https://github.com/elastic/logstash-docker
FROM docker.elastic.co/logstash/logstash:5.4.0

EXPOSE 9600:9600
EXPOSE 5000:5000
EXPOSE 5044:5044

# Add your logstash plugins setup here
# Example: RUN logstash-plugin install logstash-filter-json

COPY pipeline/logstash.conf /usr/share/logstash/pipeline
COPY grok-patterns /usr/share/logstash/pipeline/
COPY config/logstash.yml /usr/share/logstash/config/

CMD cd /usr/share/logstash/pipeline; sed -i 's/RABBIT_HOST/'"$RABBIT_HOST"'/g' logstash.conf; sed -i 's/RABBIT_USERNAME/'"$RABBIT_USERNAME"'/g' logstash.conf; sed -i 's/RABBIT_PASSWORD/'"$RABBIT_PASSWORD"'/g' logstash.conf; sed -i 's/RABBIT_VHOST/'"\/$RABBIT_VHOST"'/g' logstash.conf; logstash -f logstash.conf --config.reload.automatic;
