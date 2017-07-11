import inspect
import os
from unittest import TestCase

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
