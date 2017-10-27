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

import inspect
from unittest import TestCase
from unittest import skipIf

import os

from adapters.resources import DummyBackend

INST_ID = 'test-id-123'


class TestEPMBackend(TestCase):
    def setUp(self):
        super().setUp()
        self.dummy = DummyBackend()
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path+"/manifests/docker-compose.yml", "r") as mani:
            content = mani.read()
            self.dummy.create(instance_id=INST_ID, content=content, c_type="epm")

    def tearDown(self):
        try:
            self.dummy.delete(instance_id=INST_ID)
        except:  # yes, dirty. reason: test_delete_cmd will have already deleted the stack.
            pass

    def test_info(self):
        info = self.dummy.info(instance_id=INST_ID)
        # self.assertIsNotNone(info)

    def test_delete_cmd(self):
        self.dummy.delete(instance_id=INST_ID)


class TestEPMBackendWithoutSetup(TestCase):

    def setUp(self):
        super().setUp()
        self.dummy = DummyBackend()

    def tearDown(self):
        super().tearDown()
        self.dummy.delete(instance_id=INST_ID)

    def test_create(self):
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/manifests/docker-compose.yml", "r") as mani:
            content = mani.read()
            self.dummy.create(instance_id=INST_ID, content=content, c_type="epm")


if __name__ == '__main__':
    import unittest
    unittest.main()
    # import nose
    # nose.main()