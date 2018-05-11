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

import json
import os


import requests
import secrets
import string
import unittest

from adapters.log import get_logger, SentinelLogHandler


@unittest.skipIf(os.getenv('SENTINEL_TESTS', 'NO') != 'YES', "SENTINEL_TESTS not set in environment variables")
class TestCaseSentinelIntegration(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.admintoken = 'somevalue'  # default from compose file, take from ESM env
        self.username = ''
        self.password = ''
        self.space = ''
        self.series = ''

    def setUp(self):
        base_url = os.environ.get('ET_EMP_API', "http://localhost:9100")  # take from ESM env
        url = base_url + "/v1/api/"
        # we create randomly named users, series and sequence as there's no way to delete at the moment
        self.username = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(20)
        )  # create per user
        self.password = ''.join(
            secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(20)
        )  # create per user
        self.space = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(20)
        )  # create per service instance
        self.series = ''.join(
            secrets.choice(string.ascii_letters + string.digits) for i in range(20)
        )  # create per service instance
        msgSig = 'unixtime:s msgtype:json'  # default

        headers = {
            "Content-Type": "application/json",
            "x-auth-token": self.admintoken
        }

        # user
        data = {"login": self.username, "password": self.password}
        res = requests.post(url=url + "user/", headers=headers, data=json.dumps(data))
        self.assertEquals(res.status_code, 201)
        apikey = res.json()['apiKey']

        del headers["x-auth-token"]

        # space
        headers['x-auth-login'] = self.username
        headers['x-auth-apikey'] = apikey

        data = {"name": self.space}
        res = requests.post(url=url + "space/", headers=headers, data=json.dumps(data))
        self.assertEquals(res.status_code, 201)

        # series
        data = {"name": self.series, "spaceName": self.space, "msgSignature": msgSig}
        res = requests.post(url=url + "series/", headers=headers, data=json.dumps(data))
        self.assertEquals(res.status_code, 201)

    def test_send_string_to_sentinel(self):
        payload = 'hello_test'
        SentinelLogHandler(space=self.space, series=self.series)._send_msg(payload)

    def test_send_dict_to_sentinel(self):
        payload = {
            'date_start': 1,
            'date_end': 2
        }
        SentinelLogHandler(space=self.space, series=self.series)._send_msg(payload)

    def test_log_save_in_sentinel(self):
        logger = get_logger(__name__, 'WARN', space=self.space, series=self.series, sentinel=True)

        logger.info('just for your information!')
        logger.warning('HOI! THIS IS ME TO YOU.... HELLO!')
        logger.error('we have an oopsie!')
        logger.debug('if you\'re here there is an oopsie for sure!')

