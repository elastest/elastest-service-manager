import inspect
import os

from unittest import TestCase


from adapters.epm import DockerBackend as EPM

docker = EPM()


class TestDockerCompose(TestCase):
    def tearDown(self):
        super().tearDown()
        docker.delete(instance_id=self.inst_id)

    def setUp(self):
        super().setUp()
        self.inst_id = 'test-id-123'
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path+"/docker-compose.yml", "r") as mani:
            content = mani.read().replace("\n", "</br>")
        docker.create(instance_id=self.inst_id, content=content, type="docker-compose")

    def test_docker_info(self):
        docker.info(instance_id=self.inst_id)

    def test_docker_delete_cmd(self):
        docker.delete(instance_id=self.inst_id)


class TestDockerComposeWithoutSetup(TestCase):
    inst_id = 'test-id-123'

    def tearDown(self):
        super().tearDown()
        docker.delete(instance_id=self.inst_id)

    def test_docker_create_cmd(self):
        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/docker-compose.yml", "r") as mani:
            content = mani.read().replace("\n", "</br>")
        docker.create(instance_id=self.inst_id, content=content, type="docker-compose")
