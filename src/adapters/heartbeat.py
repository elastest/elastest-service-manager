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
from adapters.log import SentinelProducer, SentinelLogger

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

class HeartbeatMonitorException(Exception):
    def __init__(self, message, errors):
        # Call the base class constructor with the parameters it needs
        super(HeartbeatMonitorException, self).__init__(message)

        # Now for your custom code...
        self.errors = errors


class HeartbeatMonitorUtils:
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


class HeartbeatMonitor(threading.Thread):
    def __init__(self, instance_id, endpoint=''):
        self.logger = SentinelLogger.getLogger(__name__, 'WARN')
        self.instance_id = instance_id
        self.endpoint = endpoint

        # VALIDATE ENDPOINT
        result = HeartbeatMonitorUtils.validate_endpoint(self.endpoint) or True
        if result is None:
            err = 'Invalid endpoint \'{}\' provided'.format(self.endpoint)
            self.logger.warn(err)
            # raise HeartbeatMonitorException(err, errors={'instance_id': self.instance_id})

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
        print('HeartbeatMonitor created with...', self.instance_id)
        # result = HeartbeatMonitorUtils.instance_exists(self.instance_id)
        # err = 'testing instance_exists, result: \'{}\''.format(result)
        # self.logger.warn(err)
        # for i in range(1):
        #     time.sleep(5)
        #     print('running thread....')
        try:
            if not self.endpoint_is_alive():
                print('endpoint not alive')
            else:
                print('sending health status!')
        except:
            err = 'Endpoint \'{}\' for InstanceID \'{}\' is dead!'.format(self.endpoint, self.instance_id)
            print(err)
            self.logger.warn(err)
            # raise HeartbeatMonitorException(err, errors={'instance_id': self.instance_id})
