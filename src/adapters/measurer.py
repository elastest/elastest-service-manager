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
import os
from adapters.log import get_logger
from esm.util import Singleton

LOG = get_logger(__name__)


@Singleton
class MeasurerFactory:
    def __init__(self):
        self.measurers = {}

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
        self.max_retries = os.getenv('ET_AAA_ESM_SENTINEL_MAX_RETRIES', '5')

    def get_endpoint(self):
        try:
            endpoint = None  # endpoint = 'http://localhost:56567/health'  # .format(endpoint)
            inst_info = self.cache['RM'].info(instance_id=self.cache['instance_id'], manifest_type=self.cache['mani'].manifest_type)

            for k, v in inst_info.items():
                if 'Ip' in k:
                    endpoint = v
                    port = os.getenv('ET_AAA_ESM_SENTINEL_HEALTH_CHECK_PORT', '80')
                    endpoint = 'http://{}:{}/health'.format(endpoint, port)
            return endpoint
        except MeasurerException as e:
            LOG.warning(e)

    def __poll_endpoint(self):
        # Attempt to find Endpoint...
        endpoint = self.get_endpoint()

        while not endpoint and self.max_retries:
            LOG.warning('Endpoint for InstanceID \'{}\' could not be retrieved!'.format(self.cache['instance_id']))
            time.sleep(2)
            endpoint = self.get_endpoint()
            self.max_retries = self.max_retries - 1
        return endpoint

    def __endpoint_is_healthy(self):
        if self.endpoint is not None:
            response = requests.get(self.endpoint, timeout=5)
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
                LOG.info('sending health status!')
        except:
            LOG.warning('Endpoint \'{}\' for InstanceID \'{}\' is not contactable!'
                        .format(self.endpoint, self.instance_id))

    def run(self):
        super().run()
        LOG.warning('Measurer created with...{}'.format(self.instance_id))
        self.endpoint = self.__poll_endpoint()

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


class MeasurerException(Exception):
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super(MeasurerException, self).__init__(message)

        # Now for your custom code...
        self.errors = errors
