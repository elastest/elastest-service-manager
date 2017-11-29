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
from adapters.store import SQLStore
from unittest.mock import patch
# TESTS
from unittest import skipIf
import unittest
import os


# TODO: move to test_store_backends module

if os.getenv('MYSQL_TESTS', 'NO') == 'YES':
    SQLStore.set_up()


@skipIf(os.getenv('MYSQL_TESTS', 'NO') != 'YES', "MYSQL_TESTS not set in environment variables")
class TestCaseManifestManifest(unittest.TestCase):

    def test_db_connect_successful(self):
        connection = SQLStore.get_connection()
        self.assertIsNotNone(connection)
        connection.close()
        wait_time = 0
        SQLStore.set_up(wait_time)

    @patch.object(SQLStore, 'get_connection')
    def test_db_connect_not_successful(self, mock_connection):
        wait_time = 0
        mock_connection.return_value = None
        with self.assertRaises(Exception):
            SQLStore.set_up(wait_time)
