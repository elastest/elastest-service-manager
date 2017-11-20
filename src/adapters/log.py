# Copyright © 2017-2019 Zuercher Hochschule fuer Angewandte Wissenschaften.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

# import pybreaker
#
#
# class LogListener(pybreaker.CircuitBreakerListener):
#     """ Listener used to log circuit breaker events. """
#
#     def __init__(self, app):
#         self.app = app
#
#     def state_change(self, cb, old_state, new_state):
#         "Called when the circuit breaker `cb` state changes."
#         self.app.logger.error('Circuit breaker state change: %r => %r', old_state.name, new_state.name)
#
#     def failure(self, cb, exc):
#         """ This callback function is called when a function called by the
#         circuit breaker `cb` fails.
#         """
#         self.app.logger.error('Circuit breaker failure: %r, count: %r', exc, cb.fail_counter)

import json
import logging
import os
import queue

from pykafka import KafkaClient

# daiquiri.output.Syslog()
# daiquiri.output.File(directory="/var/log")
# log_outputs = [daiquiri.output.STDERR]
# daiquiri.setup( outputs=log_outputs)


def get_logger(name=None, log_level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    kafka_host = os.getenv('SENTINEL_KAFKA_EP', None)
    if kafka_host is not None:
        topic = os.getenv('SENTINEL_TOPIC', 'user-1-cyclops')
        series_name = os.getenv('SENTINEL_SERIES_NAME', 'app-logs')

        if topic is None or series_name is None:
            logger.error('Sentinel application logging configuration error. '
                         'You need to set SENTINEL_TOPIC or SENTINEL_SERIES_NAME '
                         'as environment variables to use Sentinel logging!')
        else:
            logger.info('Adding Sentinel logging handler: ep: {ep}, topic: {topic}, series name: {series_name}'
                        .format(ep=kafka_host, topic=topic, series_name=series_name))
            s_handler = SentinelLogHandler(hosts_list=kafka_host, topic=topic,
                                           series_name=series_name, batch_size=100,
                                           backup_file='backup.log')
            s_handler.setLevel(log_level)
            logger.addHandler(s_handler)

    return logger


class SentinelLogHandler(logging.Handler):
    """Kafka logger handler attempts to write python logs directly
    into specified kafka topic instead of writing them into file.
    """

    def setLevel(self, level):
        super().setLevel(level)

    def __init__(self, hosts_list, topic, series_name, batch_size=10, backup_file=None):
        logging.Handler.__init__(self)
        # Backup log file for errors
        # TODO make optional
        self.fail_fh = backup_file
        if self.fail_fh is not None:
            self.fail_fh = open(backup_file, 'w')
        kafka_client = KafkaClient(hosts_list)
        topic = kafka_client.topics[bytes(topic, 'utf-8')]

        self.producer = topic.get_producer(
            delivery_reports=True,
            min_queued_messages=batch_size,
            max_queued_messages=batch_size * 1000,
            linger_ms=15000,
            block_on_queue_full=False)
        self.count = 0
        self.series_name = bytes(series_name, 'utf-8')  # the kafka key
        self.batch_size = batch_size

    def emit(self, record):
        msg = ''
        # drop kafka logging to avoid infinite recursion
        if record.name == 'kafka':
            return
        try:
            msg_dict = dict()
            if isinstance(record, dict):
                msg_dict = {**msg_dict, **record}
            else:
                msg = self.format(record)
                msg_dict['msg'] = msg

            # mandatory fields
            msg_dict['agent'] = 'sentinel-internal-log-agent'
            msg_dict['level'] = logging.getLevelName(self.level)
            msg_dict['file'] = __file__

            msg = json.dumps(msg_dict)

            self.producer.produce(bytes(msg, 'utf-8'), partition_key=self.series_name)
            # Check on delivery reports
            self.count += 1
            if self.count > (self.batch_size * 2):
                self.check_delivery()
                self.count = 0
        except AttributeError:
            self.write_backup("Kafka Error!")
            self.write_backup(msg)
            pass
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # Log errors due queue full
            self.write_backup(msg)
            self.handleError(record)

    def check_delivery(self):
        """Checks the delivery reports from Kafka producer,
        failed reported will be written to backup file.
        """
        while True:
            try:
                msg, exc = self.producer.get_delivery_report(block=False)
                if exc is not None:
                    self.write_backup(msg)
                    self.write_backup(repr(exc))
                    # Some alert action here maybe mail
            except queue.Empty:
                break

    def write_backup(self, msg):
        if self.fail_fh:
            self.fail_fh.write(msg + "\n")

    def close(self):
        self.fail_fh.close()
        self.producer.stop()
        logging.Handler.close(self)


if __name__ == '__main__':
    kafka_host = 'kafka.demonstrator.info:9092'
    topic = 'user-1-cyclops'
    series_name = 'app-logs'

    logger = logging.getLogger(__name__)
    logger.setLevel('WARN')
    logger.info('Adding Sentinel logging handler')
    handler = SentinelLogHandler(hosts_list=kafka_host, topic=topic,
                                 series_name=series_name, batch_size=100,
                                 backup_file='backup.log')
    handler.setLevel('WARN')

    logger.addHandler(handler)
    for _ in range(10):
        logger.warning('HOI! THIS IS ME TO YOU.... HELLO!')

    d = dict()
    d['custom_thing'] = 'HOI! THIS IS ME TO YOU.... HELLO!'
    for _ in range(10):
        logger.warning(d)

    print('done.')