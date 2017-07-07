import inspect
import os
from unittest import TestCase

from adapters.resources import DockerBackend

INST_ID = 'test-id-123'


class TestDockerCompose(TestCase):
    def setUp(self):
        super().setUp()
        self.docker = DockerBackend()
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path+"/manifests/docker-compose.yml", "r") as mani:
            content = mani.read().replace("\n", "</br>")
            self.docker.create(instance_id=INST_ID, content=content, type="docker-compose")

    def tearDown(self):
        super().tearDown()
        self.docker.delete(instance_id=INST_ID)

    def test_docker_info(self):
        self.docker.info(instance_id=INST_ID)

    def test_docker_delete_cmd(self):
        self.docker.delete(instance_id=INST_ID)


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
        self.docker.create(instance_id=INST_ID, content=content, type="docker-compose")
