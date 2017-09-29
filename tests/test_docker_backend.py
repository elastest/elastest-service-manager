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
from unittest import TestCase, skipIf

import docker
import os

from adapters.resources import DockerBackend

INST_ID = 'test-id-123'


@skipIf(os.getenv('DOCKER_TESTS', 'NO') != 'YES', "DOCKER_TESTS not set in environment variables")
class TestDockerCompose(TestCase):
    def setUp(self):
        super().setUp()
        self.docker = DockerBackend()
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path+"/manifests/docker-compose.yml", "r") as mani:
            content = mani.read()
            self.docker.create(instance_id=INST_ID, content=content, c_type="docker-compose")

    def tearDown(self):
        super().tearDown()
        self.docker.delete(instance_id=INST_ID)

    def test_docker_info(self):
        self.docker.info(instance_id=INST_ID)

    def test_docker_delete_cmd(self):
        self.docker.delete(instance_id=INST_ID)


@skipIf(os.getenv('DOCKER_TESTS', 'NO') != 'YES', "DOCKER_TESTS not set in environment variables")
class TestDockerComposeWithoutSetup(TestCase):

    def setUp(self):
        super().setUp()
        self.docker = DockerBackend()

    def tearDown(self):
        super().tearDown()
        self.docker.delete(instance_id=INST_ID)

    def test_docker_create_cmd(self):
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/manifests/docker-compose.yml", "r") as mani:
            content = mani.read()
        self.docker.create(instance_id=INST_ID, content=content, c_type="docker-compose")

    def test_docker_create_cmd_with_params(self):
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/manifests/docker-compose.yml", "r") as mani:
            content = mani.read()

        params = dict()
        params['TEST'] = 'value'
        params['TEST1'] = 'value1'

        self.docker.create(instance_id=INST_ID, content=content, c_type="docker-compose", parameters=params)
        info = self.docker.info(instance_id=INST_ID)

        # this check can likely be done a better way...
        p1 = False
        p2 = False
        for k, v in info.items():
            if k.endswith('TEST'):
                p1 = True
            if k.endswith('TEST1'):
                p2 = True
        self.assertTrue(p1)
        self.assertTrue(p2)

        print('check')


@skipIf(os.getenv('DOCKER_TESTS', 'NO') != 'YES', "DOCKER_TESTS not set in environment variables")
class TestDockerBasicBackend(TestCase):
    def setUp(self):
        self.client = docker.from_env()
        self.container = None

    def tearDown(self):
        if self.container:
            try:
                self.container.kill()
                self.container.remove()
            except Exception as e:
                print(e)

    def test_docker_create(self):
        self.container = self.client.containers.run("bfirsh/reticulate-splines", detach=True)
        print(self.container)

    def test_docker_info(self):
        self.container = self.client.containers.run("bfirsh/reticulate-splines", detach=True)
        print(self.container)

    def test_docker_delete(self):
        self.container = self.client.containers.run("bfirsh/reticulate-splines", detach=True)
        print(self.container)
        self.container.kill()
        self.container.remove()


if __name__ == '__main__':
    import unittest
    unittest.main()
    # import nose
    # nose.main()
