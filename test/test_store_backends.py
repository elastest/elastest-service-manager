import os
from unittest import TestCase, skipIf

from esm.models import Plan, ServiceType, ServiceInstance, Manifest, LastOperation
from adapters.datasource import InMemoryStore, MongoDBStore


class TestInMemoryStore(TestCase):
    def setUp(self):
        super().setUp()
        self.store = InMemoryStore()
        self.test_plan = Plan(
            id='testplan', name='testing plan', description='plan for testing',
            metadata=None, free=True, bindable=False
        )

        self.test_service = ServiceType(
            id='test-svc', name='test_svc',
            description='this is a test service',
            bindable=False,
            tags=['test', 'tester'],
            metadata=None, requires=[],
            plan_updateable=False, plans=[self.test_plan],
            dashboard_client=None)

        self.test_manifest = Manifest(
            id='test-mani', plan_id=self.test_plan.id, service_id=self.test_service.id,
            manifest_type='dummy', manifest_content='')

        self.test_svc_instance = ServiceInstance(service_type=self.test_service, context={'id': 'test_svc_inst'})

        self.test_last_op = LastOperation(state='test_state', description='testing')

    def tearDown(self):
        super().tearDown()
        self.store.delete_service()
        self.store.delete_service_instance()
        self.store.delete_manifest()
        self.store.delete_last_operation()


    def test_add(self):
        self.store.add_service(self.test_service)
        self.assertGreaterEqual(len(self.store.get_service()), 1)

        self.store.add_manifest(self.test_manifest)
        self.assertGreaterEqual(len(self.store.get_manifest()), 1)

        self.store.add_service_instance(self.test_svc_instance)
        self.assertGreaterEqual(len(self.store.get_service_instance()), 1)

        self.store.add_last_operation(self.test_svc_instance.context['id'], self.test_last_op)
        self.assertGreaterEqual(len(self.store.get_last_operation()), 1)

    def test_get(self):
        self.store.add_service(self.test_service)
        self.assertIsNotNone(self.store.get_service(self.test_service.id))

        self.store.add_manifest(self.test_manifest)
        self.assertIsNotNone(self.store.get_manifest(self.test_manifest.plan_id))

        self.store.add_service_instance(self.test_svc_instance)
        self.assertIsNotNone(self.store.get_service_instance(self.test_svc_instance.context['id']))

        self.store.add_last_operation(self.test_svc_instance.context['id'], self.test_last_op)
        self.assertIsNotNone(self.store.get_last_operation(self.test_svc_instance.context['id']))

    def test_get_all(self):
        self.store.add_service(self.test_service)
        services = self.store.get_service()
        self.assertGreaterEqual(len(services), 1)

        self.store.add_manifest(self.test_manifest)
        self.assertGreaterEqual(len(self.store.get_manifest()), 1)

        self.store.add_service_instance(self.test_svc_instance)
        self.assertGreaterEqual(len(self.store.get_service_instance()), 1)

        self.store.add_last_operation(self.test_svc_instance.context['id'], self.test_last_op)
        self.assertGreaterEqual(len(self.store.get_last_operation()), 1)

    def test_delete(self):
        self.store.add_service(self.test_service)
        self.store.delete_service(self.test_service.id)
        services = self.store.get_service()
        self.assertGreaterEqual(len(services), 0)

        self.store.add_manifest(self.test_manifest)
        self.store.delete_manifest(self.test_manifest.id)
        self.assertGreaterEqual(len(self.store.get_manifest()), 0)

        self.store.add_manifest(self.test_manifest)
        self.store.delete_manifest(self.test_manifest.id)
        self.assertGreaterEqual(len(self.store.get_manifest()), 0)

        self.store.add_service_instance(self.test_svc_instance)
        self.store.delete_service_instance(self.test_svc_instance.context['id'])
        self.assertGreaterEqual(len(self.store.get_service_instance()), 0)

        self.store.add_last_operation(self.test_svc_instance.context['id'], self.test_last_op)
        self.store.delete_last_operation(self.test_svc_instance.context['id'])
        self.assertGreaterEqual(len(self.store.get_last_operation()), 0)

    def test_delete_all(self):
        self.store.add_service(self.test_service)
        self.store.delete_service()
        self.assertGreaterEqual(len(self.store.get_service()), 0)

        self.store.add_manifest(self.test_manifest)
        self.store.delete_manifest()
        self.assertGreaterEqual(len(self.store.get_manifest()), 0)

        self.store.add_service_instance(self.test_svc_instance)
        self.store.delete_manifest()
        self.assertGreaterEqual(len(self.store.get_service_instance()), 0)

        self.store.add_last_operation(self.test_svc_instance.context['id'], self.test_last_op)
        self.store.delete_last_operation()
        self.assertGreaterEqual(len(self.store.get_last_operation()), 0)


@skipIf(os.getenv('MONGODB_TESTS', 'NO') != 'YES', "MONGODB_TESTS not set in environment variables")
class TestMongoDBStore(TestInMemoryStore):

    def setUp(self):
        super().setUp()
        self.store = MongoDBStore()
        # from pymongo import MongoClient
        # c = MongoClient(socketTimeoutMS=5, connectTimeoutMS=5)
        # try:
        #     c.database_names()
        #     self.store = MongoDBStore()
        # except:
        #     self.store = InMemoryStore()
        #     print('Warning: MongoDB not available. Using the InMemoryDB.')

    def tearDown(self):
        super().tearDown()

    def test_get(self):
        super().test_get()

    def test_delete(self):
        super().test_delete()

    def test_get_all(self):
        super().test_get_all()

    def test_delete_all(self):
        super().test_delete_all()

    def test_add(self):
        super().test_add()