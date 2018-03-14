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


import re
import time
import requests
import threading
from adapters.log import get_logger, SentinelLogger

'''    
    *******************
    *******************
    **** TESTED CODE **
    *******************
    * HearbeatMonitor *
    *******************
    ******** ♥ ********
    *******************
'''

LOG = get_logger(__name__)


class MeasurerException(Exception):
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super(MeasurerException, self).__init__(message)

        # Now for your custom code...
        self.errors = errors


class MeasurerUtils:
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

        if result is None:
            err = 'Invalid endpoint \'{}\' provided'.format(endpoint)
            LOG.warning(err)

        return result


class Singleton:
    """
    A non-thread-safe helper class to ease implementing singletons.
    This should be used as a decorator -- not a metaclass -- to the
    class that should be a singleton.

    The decorated class can define one `__init__` function that
    takes only the `self` argument. Also, the decorated class cannot be
    inherited from. Other than that, there are no restrictions that apply
    to the decorated class.

    To get the singleton instance, use the `instance` method. Trying
    to use `__call__` will result in a `TypeError` being raised.

    """

    def __init__(self, decorated):
        self._decorated = decorated

    def instance(self):
        """
        Returns the singleton instance. Upon its first call, it creates a
        new instance of the decorated class and calls its `__init__` method.
        On all subsequent calls, the already created instance is returned.

        """
        try:
            return self._instance
        except AttributeError:
            self._instance = self._decorated()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `instance()`.')

    def __instancecheck__(self, inst):
        return isinstance(inst, self._decorated)


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
    def __init__(self, cache):
        self.cache = cache
        self.instance_id = cache['instance_id']
        self._stop_event = threading.Event()
        self.stop()

        self.endpoint = None
        threading.Thread.__init__(self)

    def get_endpoint(self):
        endpoint = None
        inst_info = self.cache['RM'].info(instance_id=self.cache['instance_id'], manifest_type=self.cache['mani'].manifest_type)

        for k, v in inst_info.items():
            if 'Ip' in k:
                endpoint = v
                endpoint = 'http://{}:56567/health'.format(endpoint)
        return endpoint

    def poll_endpoint(self):
        # Attempt to find Endpoint...
        endpoint = self.get_endpoint()
        MAX_RETRIES = 5
        while not endpoint and MAX_RETRIES:
            time.sleep(2)
            err = 'Endpoint for InstanceID \'{}\' could not be retrieved!'.format(self.cache['instance_id'])
            LOG.warning(err)
            MAX_RETRIES = MAX_RETRIES - 1
        return endpoint

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

    '''
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

    '''

    def endpoint_is_alive(self):
        if self.endpoint != None:
            response = requests.get(self.endpoint)
            data = response.json()
            return data['status'] == 'up'

        else:
            return False

    def measure_alive(self):
        print('checking alive...')
        try:
            if not self.endpoint_is_alive():
                print('endpoint not alive')
            else:
                print('sending health status!')
        except:
            err = 'Endpoint \'{}\' for InstanceID \'{}\' is dead!'.format(self.endpoint, self.instance_id)
            LOG.warning(err)

    def run(self):
        LOG.warning('Measurer created with...{}'.format(self.instance_id))
        self.endpoint = self.poll_endpoint()
        # VALIDATE ENDPOINT
        valid = MeasurerUtils.validate_endpoint(self.endpoint) or True
        while valid and not self.stopped():
            time.sleep(2)
            LOG.warning('stopped status...,{}'.format(self.stopped()))
            stopped = 'stopped status...{}'.format(self.stopped())
            print(stopped)
            # MEASURE HEARTBEAT
            self.measure_alive()

