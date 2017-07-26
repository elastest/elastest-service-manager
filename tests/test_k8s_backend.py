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

import os

from adapters.resources import KubernetesBackend

INST_ID = 'test-id-123'


class TestK8SBackend(TestCase):
    def setUp(self):
        super().setUp()
        self.k8s = KubernetesBackend()
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path+"/manifests/k8s_basic.yml", "r") as mani:
            content = mani.read().replace("\n", "</br>")
            self.k8s.create(instance_id=INST_ID, content=content, c_type="kubernetes")

    def tearDown(self):
        pass

    def test_docker_info(self):
        pass

    def test_docker_delete_cmd(self):
        pass


class TestK8SBackendWithoutSetup(TestCase):

    def setUp(self):
        super().setUp()
        self.k8s = KubernetesBackend()

    def tearDown(self):
        super().tearDown()
        # self.k8s.delete(instance_id=INST_ID)

    def test_k8s_create(self):
        pass


if __name__ == '__main__':
    import unittest
    unittest.main()
    # import nose
    # nose.main()