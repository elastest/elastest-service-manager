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

from adapters.log import get_logger, SentinelAgentInjector

LOG = get_logger(__name__)

import os
from adapters.resources import KubernetesBackend

INST_ID = 'test-id-123'

@skipIf(os.getenv('KUBERNETES_TESTS', 'NO') != 'YES', "KUBERNETES_TESTS not set in environment variables")
class TestK8SBackend(TestCase):
    def setUp(self):
        LOG.info("--------- TEST START --------")
        super().setUp()
        self.k8s = KubernetesBackend()

    def tearDown(self):
        LOG.info("--------- TEST END --------")

    def test_end2end_with_create_twice(self):
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        print(path)
        with open(path + "/manifests/k8s_simple.yml", "r") as mani:
            # content = mani.read().replace("\n", " </br>")

            # test create
            self.content = mani
            outcome = self.k8s.create(instance_id=INST_ID, content=self.content, c_type="kubernetes")
            self.assertEqual(True, outcome)

            # test create when existing
            self.content = mani
            outcome = self.k8s.create(instance_id=INST_ID, content=self.content, c_type="kubernetes")
            self.assertEqual(False, outcome)

            # test delete
            import time
            time.sleep(10)
            outcome = self.k8s.delete(instance_id=INST_ID, c_type="kubernetes")
            self.assertEqual(True, outcome)

    def test_create_with_null_manifest(self):
        mani = None
        # test create
        self.content = mani
        outcome = self.k8s.create(instance_id=INST_ID, content=self.content, c_type="kubernetes")
        self.assertEqual(False, outcome)

    def test_create_with_no_manifest(self):
        # the k8s backend creates their own diretory and file, so this error is not viable
        pass

    def test_create_with_invalid_manifest(self):
        mani = "dumdum"
        # test create
        self.content = mani
        outcome = self.k8s.create(instance_id=INST_ID, content=self.content, c_type="kubernetes")
        LOG.info("outcome: {}".format(outcome))
        self.assertEqual(False, outcome)

    def test_delete_non_existent(self):
        outcome = self.k8s.delete(instance_id=INST_ID, c_type="kubernetes")
        self.assertEqual(False, outcome)

    def test_delete_non_existent(self):
        outcome = self.k8s.delete(instance_id=None, c_type="kubernetes")
        self.assertEqual(False, outcome)

    def test_docker_info(self):
        info = self.k8s.info(instance_id=None)
        LOG.info("Info retrieved: {}".format(info))

    def test_empty_delete(self):
        outcome = self.k8s.delete(instance_id=INST_ID, c_type="kubernetes")
        self.assertEqual(False, outcome)


@skipIf(os.getenv('KUBERNETES_TESTS', 'NO') != 'NO', "Kubernetes Tests set to run, skipping OFFLINE tests.")
class TestK8SBackendOffline(TestCase):

    def test_create_not_responding(self):
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/manifests/k8s_simple.yml", "r") as mani:
            with self.assertRaises(Exception):
                # test create
                self.content = mani
                outcome = self.k8s.create(instance_id=INST_ID, content=self.content, c_type="kubernetes")

    def test_delete_not_responding(self):
        with self.assertRaises(Exception):
            # test delete
            outcome = self.k8s.delete(instance_id=INST_ID, c_type="kubernetes")
            self.assertEqual(False, outcome)


if __name__ == '__main__':
    import unittest
    unittest.main()
