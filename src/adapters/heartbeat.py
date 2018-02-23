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

from threading import Thread
import time
import re
import threading
import requests
from esm.controllers.service_instances_controller import instance_info, _get_instance
from adapters.sentinel import SentinelProducer, SentinelLogger


class HeartBeatMonitorException(Exception):
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super(HeartBeatMonitorException, self).__init__(message)

        # Now for your custom code...
        self.errors = errors


class HeartBeatMonitor(threading.Thread):
    logger = SentinelLogger.getLogger(__name__, 'WARN')

    def __init__(self, instance_id, endpoint=None):
        # OBTAIN ENDPOINT
        self.instance_id = instance_id
        self.endpoint = endpoint
        self.endpoint = self.obtain_endpoint()
        # VALIDATE ENDPOINT
        self.validate_endpoint()

        threading.Thread.__init__(self)

    '''
        HeartBeatMonitor Sequence

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
    def instance_exists(self):
        instance, result = instance_info(self.instance_id)
        if result == 200:
            return True
        else:
            return False

    def get_instance_items(self):
        return _get_instance(instance_info(self.instance_id)).get_items()

    def validate_endpoint(self):
        regex = re.compile(
            r'^(?:http|ftp)s?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        SentinelProducer.send_msg('obtain_endpoint gives {}'.format(self.obtain_endpoint()))
        SentinelProducer.send_msg('my_endpoint is {}'.format(self.endpoint))
        result = regex.match(self.endpoint)
        if result is None:
            err = 'Invalid endpoint {} provided'.format(self.endpoint)
            self.logger.warn(err)
            raise HeartBeatMonitorException(err, errors={'instance_id': self.instance_id})

    def obtain_endpoint(self):
        # for i in range(100):
        for attempt in range(10):
            try:
                if self.instance_exists():
                    for k, v in self.get_instance_items():
                        if 'Ip' in k:
                            return v
                    err = '<IP key> not found in instance_dict {}'.format(self.instance_id)
                    self.logger.warn(err)
                    raise HeartBeatMonitorException(message=err, errors={'instance_id': self.instance_id})
                else:
                    err = '<Instance> not found for {}'.format(self.instance_id)
                    self.logger.warn(err)
                    raise HeartBeatMonitorException(err, errors={'instance_id': self.instance_id})
            except:
                err = '<Instance> not found for {}'.format(self.instance_id)
                self.logger.warn(err)
                raise HeartBeatMonitorException(err, errors={'instance_id': self.instance_id})

        err = 'Attempts expired. Endpoint for instance {} is not alive.'.format(self.instance_id)
        self.logger.warn(err)
        return None

    def endpoint_is_alive(self):
        response = requests.get(self.endpoint)
        data = response.json()
        return data['health'] == 200

    def run(self):
        while 1:
            time.sleep(5)
            if not self.endpoint_is_alive():
                err = 'Endpoint {} for InstanceID {} is dead!'.format(self.endpoint, self.instance_id)
                self.logger.warn(err)
                raise HeartBeatMonitorException(err, errors={'instance_id': self.instance_id})
