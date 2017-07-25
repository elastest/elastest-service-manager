FROM library/rabbitmq:3.5.1-management

EXPOSE 15672:15672
EXPOSE 5672:5672

# Add script to create default users / vhosts
COPY init.sh /init.sh

# Set correct executable permissions
RUN chmod +x /init.sh

# Define default command
CMD ["/init.sh"]
