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

import jsonpickle
import logging
import os
from time import sleep

from kafka import KafkaProducer


def get_logger(name, level=logging.DEBUG, space=None, series=None, sentinel=False):  # pragma: sentinel NO cover
    if os.environ.get('ESM_SENTINEL_KAFKA_ENDPOINT', '') != '' and sentinel:
        logger = logging.getLogger(name)
        logger.setLevel(level)

        logger.info('Adding Sentinel logging handler')
        handler = SentinelLogHandler(backup_file='backup.log', space=space, series=series)
        handler.setLevel(level)
        logger.addHandler(handler)

        print('reading...', os.environ.get('ESM_SENTINEL_TOPIC', None))
    else:
        logging.basicConfig(level=level)
        logger = logging.getLogger(name)

    logger.setLevel(level)
    return logger


class SentinelLogHandler(logging.Handler):  # pragma: sentinel NO cover
    """Kafka logger handler attempts to write python logs directly
    into specified kafka topic instead of writing them into file.
    """

    def setLevel(self, level):
        super().setLevel(level)

    def __init__(self, backup_file=None, space=None, series=None):
        logging.Handler.__init__(self)
        self.space = space
        self.series = series
        # Backup log file for errors
        self.fail_fh = backup_file
        if self.fail_fh is not None:
            self.fail_fh = open(backup_file, 'w')

    @staticmethod
    def format_msg(record):
        msg_dict = {}
        msg_dict['level'] = 'WARN'  # logging.getLevelName(self.level)
        msg_dict['msg'] = record

        return msg_dict

    def emit(self, record):
        # drop kafka logging to avoid infinite recursion
        if record.name == 'kafka':
            return
        try:
            print('emitting...', record.msg)
            msg_dict = {'msg': record.msg}
            if '#' in record.msg:
                msg_dict['instance_id'], msg_dict['msg'] = record.msg.split('#')
            msg_dict['level'] = logging.getLevelName(self.level)
            msg_dict['file'] = __file__

            # msg = self.format_msg(record)
            print('Preparing to send log-payload: ', msg_dict)
            self._send_msg(msg_dict)

        except AttributeError:
            self.write_backup("Kafka Error!")
            self.write_backup(record)
            pass

        except (KeyboardInterrupt, SystemExit):
            raise

        except:
            # Log errors due queue full
            self.write_backup(record)
            self.handleError(record)

    def write_backup(self, record):
        if self.fail_fh:
            self.fail_fh.write(str(record) + "\n")

    def close(self):
        if self.fail_fh:
            self.fail_fh.close()
        logging.Handler.close(self)

    def _get_kafka_producer(self, endpoint, key_serializer, value_serializer):
        if key_serializer == "StringSerializer" and value_serializer == "StringSerializer":
            return KafkaProducer(linger_ms=1, acks='all', retries=0, key_serializer=str.encode,
                                 value_serializer=str.encode, bootstrap_servers=[endpoint])

    def _send_msg(self, payload):
        msg_dict = dict()
        msg_dict["agent"] = os.environ.get('ESM_SENTINEL_AGENT', 'sentinel-internal-log-agent')

        if type(payload) == dict:
            msg_dict = {**msg_dict, **payload}
        elif type(payload) == str:
            msg_dict['msg'] = payload

        print('sending...', msg_dict)
        msg = jsonpickle.encode(msg_dict)
        kafka_producer = self._get_kafka_producer(os.environ.get('ESM_SENTINEL_KAFKA_ENDPOINT', None),
                                                             os.environ.get('ESM_SENTINEL_KAFKA_KEY_SERIALIZER',
                                                                            'StringSerializer'),
                                                             os.environ.get('ESM_SENTINEL_KAFKA_VALUE_SERIALIZER',
                                                                            'StringSerializer'))
        if self.space is not None and self.series is not None:
            kafka_producer.send(self.space, key=self.series, value=msg)
        else:
            kafka_producer.send(os.environ.get('ESM_SENTINEL_TOPIC', None),  # space
                                key=os.environ.get('ESM_SENTINEL_SERIES_NAME', None),  # series
                                value=msg)
        # time required for kafka to get the value
        sleep(0.05)
        kafka_producer.close()
