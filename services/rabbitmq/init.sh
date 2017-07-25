#!/bin/sh

# Create Default RabbitMQ setup
( sleep 10 ; \

# Create users
# rabbitmqctl add_user <username> <password>
rabbitmqctl add_user ${RABBIT_USERNAME} ${RABBIT_PASSWORD} ; \

# Set user rights
# rabbitmqctl set_user_tags <username> <tag>
rabbitmqctl set_user_tags ${RABBIT_USERNAME} administrator ; \

# Create vhosts
# rabbitmqctl add_vhost <vhostname>
rabbitmqctl add_vhost /${RABBIT_VHOST} ; \

# Set vhost permissions
# rabbitmqctl set_permissions -p <vhostname> <username> ".*" ".*" ".*"
rabbitmqctl set_permissions -p /${RABBIT_VHOST} ${RABBIT_USERNAME} ".*" ".*" ".*" ; \

#rabbitmq-plugins enable rabbitmq_stomp; \     
) &    
rabbitmq-server $@
