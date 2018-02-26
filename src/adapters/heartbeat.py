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

import threading
from sentinel import SentinelLogger, SentinelProducer
import requests
import time
import re


class HeartBeatMonitorException(Exception):
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super(HeartBeatMonitorException, self).__init__(message)

        # Now for your custom code...
        self.errors = errors


class HeartbeatMonitorUtils:
    # @staticmethod
    # def instance_exists(self, instance_id):
    #     instance, result = instance_info(instance_id)
    #     if result == 200:
    #         return True
    #     else:
    #         return False
    #
    # @staticmethod
    # def get_instance_items(self, instance_id):
    #     return _get_instance(instance_info(instance_id)).context.items()

    # @staticmethod
    # def obtain_endpoint(instance_id):
    #     # for i in range(100):
    #     for attempt in range(10):
    #         try:
    #             if HeartbeatMonitorUtils.instance_exists(instance_id):
    #                 for k, v in HeartbeatMonitorUtils.get_instance_items():
    #                     if 'Ip' in k:
    #                         return v
    #                 err = '<IP key> not found in instance_dict {}'.format(instance_id)
    #                 self.logger.warn(err)
    #                 raise HeartbeatMonitorException(message=err, errors={'instance_id': instance_id})
    #             else:
    #                 err = '<Instance> not found for {}'.format(instance_id)
    #                 self.logger.warn(err)
    #                 raise HeartbeatMonitorException(err, errors={'instance_id': instance_id})
    #         except:
    #             err = '<Instance> not found for {}'.format(instance_id)
    #             self.logger.warn(err)
    #             raise HeartbeatMonitorException(err, errors={'instance_id': instance_id})
    #
    #     err = 'Attempts expired. Endpoint for instance {} is not alive.'.format(instance_id)
    #     self.logger.warn(err)
    #     return None

    @staticmethod
    def validate_endpoint(endpoint):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        # SentinelProducer.send_msg('obtain_endpoint gives {}'.format(self.obtain_endpoint()))
        # SentinelProducer.send_msg('my_endpoint is {}'.format(self.endpoint))
        result = regex.match(endpoint)
        return result


class HeartBeatMonitor(threading.Thread):
    def __init__(self, instance_id, endpoint=''):
        self.logger = SentinelLogger.getLogger(__name__, 'WARN')
        self.instance_id = instance_id
        self.endpoint = endpoint

        # VALIDATE ENDPOINT
        result = HeartbeatMonitorUtils.validate_endpoint(self.endpoint)
        if result is None:
            err = 'Invalid endpoint \'{}\' provided'.format(self.endpoint)
            self.logger.warn(err)
            raise HeartBeatMonitorException(err, errors={'instance_id': self.instance_id})

        threading.Thread.__init__(self)

    '''
        HeartbeatMonitor Sequence

        :arg instance_id
        > obtain_endpoint (attempts)
            > instance_exists
            :exception Instance_NotFound
            > get_instance_dict
            :exception IPKey_NotFound
        :exception EndpointNeverAlive

        > validate_endpoint
        :exception InvalidEndpoint

    '''

    def endpoint_is_alive(self):
        response = requests.get(self.endpoint)
        data = response.json()
        return data['status'] == 'up'

    def run(self):
        for i in range(1):
            time.sleep(5)
            print('running thread....')
            try:
                if not self.endpoint_is_alive():
                    print('endpoint not alive')
                else:
                    print('sending health status!')
            except:
                err = 'Endpoint \'{}\' for InstanceID \'{}\' is dead!'.format(self.endpoint, self.instance_id)
                self.logger.warn(err)
                raise HeartBeatMonitorException(err, errors={'instance_id': self.instance_id})
