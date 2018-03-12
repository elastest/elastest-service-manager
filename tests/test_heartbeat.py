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

import unittest
from unittest import skipIf
from adapters.heartbeat import HeartbeatMonitor, HeartbeatMonitorException
from unittest.mock import patch
from adapters.heartbeat import SentinelProducer, SentinelLogger
import os


@skipIf(os.getenv('HEARTBEAT_TESTS', 'NO') != 'YES', "HEARTBEAT_TESTS not set in environment variables")
class TestCaseHeartBeatMonitor(unittest.TestCase):
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

    # @patch.object(HeartBeatMonitor, 'instance_exists')
    # def test_instance_not_found(self, mock_instance_exists):
    #     mock_instance_exists.return_value = False
    #     with self.assertRaises(HeartbeatMonitorException):
    #         HeartBeatMonitor('instance_id').obtain_endpoint()

    @patch.object(HeartbeatMonitor, 'instance_exists')
    @patch.object(HeartbeatMonitor, 'get_instance_items')
    def test_ip_key_not_found(self, mock_instance_exists, mock_get_instance_items):
        mock_instance_exists.return_value = True
        mock_get_instance_items.return_value = {"foo": "bar"}
        with self.assertRaises(HeartbeatMonitorException):
            HeartbeatMonitor('instance_id').obtain_endpoint()

    @patch.object(HeartbeatMonitor, 'instance_exists')
    def test_endpoint_never_alive(self, mock_instance_exists):
        mock_instance_exists.return_value = False
        with self.assertRaises(HeartbeatMonitorException):
            result = HeartbeatMonitor('instance_id').obtain_endpoint()
            self.assertIsNone(result)

    @patch.object(HeartbeatMonitor, 'instance_exists')
    @patch.object(HeartbeatMonitor, 'obtain_endpoint')
    @patch.object(HeartbeatMonitor, 'endpoint_is_alive')
    def test_endpoint_never_alive(self, mock_instance_exists, mock_obtain_endpoint, endpoint_is_alive):
        mock_instance_exists.return_value = False
        mock_obtain_endpoint.return_value = "fake-endpoint"
        endpoint_is_alive.return_value = False
        with self.assertRaises(HeartbeatMonitorException):
            HeartbeatMonitor('instance_id').validate_endpoint()

    # @patch.object(HeartBeatMonitor, 'instance_exists')
    # @patch.object(HeartBeatMonitor, 'obtain_endpoint')
    # @patch.object(HeartBeatMonitor, 'endpoint_is_alive')
    # def test_endpoint_never_alive(self, instance_exists, obtain_endpoint, endpoint_is_alive):
    #     instance_exists.return_value = False
    #     obtain_endpoint.return_value = "http://mybrokenlink.com"
    #     endpoint_is_alive.return_value = False
    #     with self.assertRaises(HeartbeatMonitorException):
    #         HeartBeatMonitor('instance_id').start()
