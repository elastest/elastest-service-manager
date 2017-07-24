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

import os
from unittest import TestCase, skipIf

from esm.models import Plan, ServiceType, ServiceInstance, Manifest, LastOperation
from adapters.datasource import InMemoryStore, MongoDBStore, Store


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
        # add
        self.store.add_service(self.test_service)
        self.assertGreaterEqual(len(self.store.get_service()), 1)
        # update
        self.store.add_service(self.test_service)
        self.assertGreaterEqual(len(self.store.get_service()), 1)

        # add
        self.store.add_manifest(self.test_manifest)
        self.assertGreaterEqual(len(self.store.get_manifest()), 1)
        # update
        self.store.add_manifest(self.test_manifest)
        self.assertGreaterEqual(len(self.store.get_manifest()), 1)

        # add
        self.store.add_service_instance(self.test_svc_instance)
        self.assertGreaterEqual(len(self.store.get_service_instance()), 1)
        # update
        self.store.add_service_instance(self.test_svc_instance)
        self.assertGreaterEqual(len(self.store.get_service_instance()), 1)

        # add
        self.store.add_last_operation(self.test_svc_instance.context['id'], self.test_last_op)
        self.assertGreaterEqual(len(self.store.get_last_operation()), 1)
        # update
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
        mongo_host = os.getenv('ESM_MONGO_HOST', 'localhost')
        self.store = MongoDBStore(host=mongo_host)

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


class TestStore(TestCase):
    def setUp(self):
        self.store = Store()

    def test_get(self):
        with self.assertRaises(NotImplementedError):
            self.store.get_service()
        with self.assertRaises(NotImplementedError):
            self.store.get_manifest()
        with self.assertRaises(NotImplementedError):
            self.store.get_service_instance()
        with self.assertRaises(NotImplementedError):
            self.store.get_last_operation()

    def test_delete(self):
        with self.assertRaises(NotImplementedError):
            self.store.delete_service()
        with self.assertRaises(NotImplementedError):
            self.store.delete_manifest()
        with self.assertRaises(NotImplementedError):
            self.store.delete_service_instance()
        with self.assertRaises(NotImplementedError):
            self.store.delete_last_operation()

    def test_add(self):
        with self.assertRaises(NotImplementedError):
            self.store.add_service(service=None)
        with self.assertRaises(NotImplementedError):
            self.store.add_manifest(manifest=None)
        with self.assertRaises(NotImplementedError):
            self.store.add_service_instance(service_instance=None)
        with self.assertRaises(NotImplementedError):
            self.store.add_last_operation(instance_id='', last_operation=None)


if __name__ == '__main__':
    import unittest
    unittest.main()