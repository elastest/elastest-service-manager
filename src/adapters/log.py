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
# GENERICS
import os

'''    
    *******************
    *******************
    **** TESTED CODE **
    *******************
    ** SentinelLogger *
    *******************
    ******** ♥ ********
    *******************
'''

from kafka import KafkaProducer
import jsonpickle
from time import sleep
import logging


def get_logger(name, level=logging.DEBUG):
    if os.environ.get('ET_AAA_ESM_SENTINEL_EP', '') != '':
        logger = SentinelLogger.getLogger(name, level)
        logger.warning(os.getenv('ET_AAA_ESM_SENTINEL_TOPIC', None))
        print('reading...', os.getenv('ET_AAA_ESM_SENTINEL_TOPIC', None))
    else:
        logging.basicConfig(level=level)
        logger = logging.getLogger(name)

    logger.setLevel(level)
    return logger


class SentinelLogger:
    @staticmethod
    def getLogger(name, level='WARN'):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        logger.info('Adding Sentinel logging handler')
        if os.environ.get('ET_AAA_ESM_SENTINEL_EP', '') != '':
            handler = SentinelLogHandler(backup_file='backup.log')
            handler.setLevel(level)
            logger.addHandler(handler)

        return logger


class SentinelProducer:
    @staticmethod
    def get_kafka_producer(endpoint, key_serializer, value_serializer):
        if key_serializer == "StringSerializer" and value_serializer == "StringSerializer":
            return KafkaProducer(linger_ms=1, acks='all', retries=0, key_serializer=str.encode,
                                 value_serializer=str.encode, bootstrap_servers=[endpoint])

    @staticmethod
    def send_msg(payload):
        msg_dict = {}
        msg_dict["agent"] = os.getenv('ET_AAA_ESM_SENTINEL_AGENT', None)

        if type(payload) == dict:
            msg_dict = {**msg_dict, **payload}
        elif type(payload) == str:
            msg_dict['msg'] = payload

        print('sending...', msg_dict)
        msg = jsonpickle.encode(msg_dict)
        kafka_producer = SentinelProducer.get_kafka_producer(os.getenv('ET_AAA_ESM_SENTINEL_KAFKA_ENDPOINT', None),
                                                             os.getenv('ET_AAA_ESM_SENTINEL_KAFKA_KEY_SERIALIZER', None),
                                                             os.getenv('ET_AAA_ESM_SENTINEL_KAFKA_VALUE_SERIALIZER', None))

        kafka_producer.send(os.getenv('ET_AAA_ESM_SENTINEL_TOPIC', None),
                            key=os.getenv('ET_AAA_ESM_SENTINEL_SERIES_NAME', None),
                            value=msg)
        # time required for kafka to get the value
        sleep(0.05)
        kafka_producer.close()


class SentinelLogHandler(logging.Handler):
    """Kafka logger handler attempts to write python logs directly
    into specified kafka topic instead of writing them into file.
    """

    def setLevel(self, level):
        super().setLevel(level)

    def __init__(self, backup_file=None):
        logging.Handler.__init__(self)
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
            print('logging received', record.msg)
            msg_dict = {'msg': record.msg}
            msg_dict['level'] = logging.getLevelName(self.level)
            msg_dict['file'] = __file__

            # msg = self.format_msg(record)
            print('emitting, ', msg_dict)
            SentinelProducer.send_msg(msg_dict)

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

    def write_backup(self, msg):
        if self.fail_fh:
            self.fail_fh.write(msg + "\n")

    def close(self):
        if self.fail_fh:
            self.fail_fh.close()
        # SentinelProducer.producer.close()
        logging.Handler.close(self)
