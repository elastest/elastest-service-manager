import inspect
import os
from unittest import TestCase, skipIf, skip

import docker

from adapters.resources import DockerBackend

INST_ID = 'test-id-123'


@skipIf(os.getenv('DOCKER_TESTS', 'NO') != 'YES', "DOCKER_TESTS not set in environment variables")
class TestDockerCompose(TestCase):
    def setUp(self):
        super().setUp()
        self.docker = DockerBackend()
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path+"/manifests/docker-compose.yml", "r") as mani:
            content = mani.read().replace("\n", "</br>")
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
            content = mani.read().replace("\n", "</br>")
        self.docker.create(instance_id=INST_ID, content=content, c_type="docker-compose")


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
