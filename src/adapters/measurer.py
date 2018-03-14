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


import time
import requests
import threading

from adapters.log import get_logger
from esm.util import Singleton

LOG = get_logger(__name__)


@Singleton
class MeasurerFactory:
    def __init__(self):
        self.measurers = {}

    # TODO we should only add and remove from the measurers hash, not activate the thread here.
    def start_heartbeat_measurer(self, cache):
        measurer = Measurer(cache)
        measurer.start()
        self.measurers[cache['instance_id']] = measurer

    def stop_heartbeat_measurer(self, instance_id):
        self.measurers[instance_id].stop()


class Measurer(threading.Thread):
    """
        Measurer Sequence

        :arg instance_id
        > obtain_endpoint (attempts)
            > instance_exists
            :exception Instance_NotFound
            > get_instance_dict
            :exception IPKey_NotFound
        :exception EndpointNeverAlive

        > validate_endpoint
        :exception InvalidEndpoint
    """

    def __init__(self, cache):
        super(Measurer, self).__init__()
        self.cache = cache
        self.instance_id = cache['instance_id']
        self._stop_event = threading.Event()
        self.endpoint = None
        self.max_retries = 5  # TODO make configurable

    def __get_endpoint(self):
        endpoint = None  # endpoint = 'http://localhost:56567/health'  # .format(endpoint)
        inst_info = self.cache['RM'].info(instance_id=self.cache['instance_id'], manifest_type=self.cache['mani'].manifest_type)

        for k, v in inst_info.items():
            if 'Ip' in k:
                endpoint = v
                # TODO fix hardcoded port number
                endpoint = 'http://{}:56567/health'.format(endpoint)
        return endpoint

    def __poll_endpoint(self):
        # Attempt to find Endpoint...
        endpoint = self.__get_endpoint()

        while not endpoint and self.max_retries:
            LOG.warning('Endpoint for InstanceID \'{}\' could not be retrieved!'.format(self.cache['instance_id']))
            time.sleep(2)
            endpoint = self.__get_endpoint()
            self.max_retries = self.max_retries - 1
        return endpoint

    def __endpoint_is_healthy(self):
        # TODO returns multiple types (string and boolean) - settle on one!
        if self.endpoint is not None:
            response = requests.get(self.endpoint)
            data = response.json()
            return data['status'] == 'up'

        else:
            return False

    def __measure_health(self):
        LOG.info('Checking instance...')
        try:
            if not self.__endpoint_is_healthy():
                LOG.warning('Instance endpoint is not alive')
            else:
                # TODO send to where? EMP(Sentinel) I presume
                LOG.info('sending health status!')
        except:
            LOG.warning('Endpoint \'{}\' for InstanceID \'{}\' is not contactable!'
                        .format(self.endpoint, self.instance_id))

    def run(self):
        super().run()
        LOG.warning('Measurer created with...{}'.format(self.instance_id))
        self.endpoint = self.__poll_endpoint()

        # TODO not necessary ATM
        # VALIDATE ENDPOINT
        # valid = MeasurerUtils.validate_endpoint(self.endpoint) or True
        # valid = True
        while not self.is_stopped():
            time.sleep(2)
            LOG.warning('stopped status...,{}'.format(self.is_stopped()))
            self.__measure_health()  # measure service's health

    def stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()


# class MeasurerException(Exception):
#     def __init__(self, message, errors):
#         # Call the base class constructor with the parameters it needs
#         super(MeasurerException, self).__init__(message)
#
#         # Now for your custom code...
#         self.errors = errors


# import re
# class MeasurerUtils:
#     @staticmethod
#     def validate_endpoint(endpoint):
#         regex = re.compile(
#             r'^(?:http|ftp)s?://'  # http:// or https://
#             r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
#             r'localhost|'  # localhost...
#             r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
#             r'(?::\d+)?'  # optional port
#             r'(?:/?|[/?]\S+)$', re.IGNORECASE)
#
#         # SentinelProducer.send_msg('obtain_endpoint gives {}'.format(self.obtain_endpoint()))
#         # SentinelProducer.send_msg('my_endpoint is {}'.format(self.endpoint))
#         result = regex.match(endpoint)
#
#         if result is None:
#             err = 'Invalid endpoint \'{}\' provided'.format(endpoint)
#             LOG.warning(err)
#
#         return result
