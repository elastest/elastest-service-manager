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

import config
from adapters.log import get_logger
from esm.util import Singleton


LOG = get_logger(__name__, 'WARN', space=config.esm_hc_sen_topic, series=config.esm_hc_sen_series, sentinel=True)


@Singleton
class MeasurerFactory:  # pragma: no cover

    def __init__(self):
        self.measurers = {}

    def start_heartbeat_measurer(self, cache):
        measurer = Measurer(cache)
        measurer.start()
        self.measurers[cache['instance_id']] = measurer

    def stop_heartbeat_measurer(self, instance_id):
        self.measurers[instance_id].stop()


class Measurer(threading.Thread):  # pragma: no cover

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
        self.max_retries = config.esm_hc_sen_max_retries

    def get_endpoint(self):
        try:
            endpoint = None  # endpoint = 'http://localhost:56567/health'  # .format(endpoint)
            inst_info = self.cache['RM'].info(instance_id=self.cache['instance_id'], manifest_type=self.cache['mani'].manifest_type)
            LOG.debug("inst_info: {}".format(inst_info))
            for k, v in inst_info.items():
                if 'Ip' in k:
                    endpoint = v
                    port = config.esm_hc_sen_hc_port
                    endpoint = 'http://{}:{}/health'.format(endpoint, port)
            return endpoint
        except MeasurerException as e:
            LOG.warning(e)

    def __poll_endpoint(self):
        # Attempt to find Endpoint...
        endpoint = self.get_endpoint()

        while not endpoint and self.max_retries:
            LOG.warning('{}#Endpoint could not be retrieved!'.format(self.cache['instance_id']))
            time.sleep(2)
            endpoint = self.get_endpoint()
            self.max_retries = self.max_retries - 1
        return endpoint

    def __endpoint_is_healthy(self):
        if self.endpoint is not None:
            response = requests.get(self.endpoint, timeout=5)
            data = response.json()
            return data.get('status') == 'up'

        else:
            return False

    def __measure_health(self):
        LOG.info('Checking instance...')
        try:
            if not self.__endpoint_is_healthy():
                LOG.warning('{}#Endpoint \'{}\' is down!'
                        .format(self.instance_id, self.endpoint))
            else:
                LOG.warning('{}#Endpoint \'{}\' is alive!'
                        .format(self.instance_id, self.endpoint))
        except:
            LOG.warning('{}#Endpoint \'{}\' is unreachable!'
                        .format(self.instance_id, self.endpoint))

    def run(self):
        super().run()
        LOG.warning('{}#Measurer created'.format(self.instance_id))
        self.endpoint = self.__poll_endpoint()
        LOG.debug("running measurer, endpoint found {}".format(self.endpoint))

        # VALIDATE ENDPOINT
        # valid = MeasurerUtils.validate_endpoint(self.endpoint) or True
        # valid = True
        while not self.is_stopped():
            periodicity = config.esm_hc_interval
            self.__measure_health()
            time.sleep(int(periodicity))

    def stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()


class MeasurerException(Exception):  # pragma: no cover
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super(MeasurerException, self).__init__(message)

        # Now for your custom code...
        self.errors = errors
