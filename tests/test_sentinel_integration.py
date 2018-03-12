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
# TESTS

from unittest import skipIf
import unittest
from adapters.log import get_logger, SentinelProducer
import os


@skipIf(os.getenv('SENTINEL_TESTS', 'NO') != 'YES', "SENTINEL_TESTS not set in environment variables")
class TestCaseSentinelIntegration(unittest.TestCase):
    def test_send_string_to_sentinel(self):
        payload = 'hello_test'
        SentinelProducer.send_msg(payload)

    def test_send_dict_to_sentinel(self):
        payload = {
            'date_start': 1,
            'date_end': 2
        }
        SentinelProducer.send_msg(payload)

    def test_log_save_in_sentinel(self):
        logger = get_logger(__name__, 'WARN')
        logger.warning('HOI! THIS IS ME TO YOU.... HELLO!')
