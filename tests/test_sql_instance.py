# # Copyright © 2017-2019 Zuercher Hochschule fuer Angewandte Wissenschaften.
# # All Rights Reserved.
# #
# #    Licensed under the Apache License, Version 2.0 (the "License"); you may
# #    not use this file except in compliance with the License. You may obtain
# #    a copy of the License at
# #
# #         http://www.apache.org/licenses/LICENSE-2.0
# #
# #    Unless required by applicable law or agreed to in writing, software
# #    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# #    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# #    License for the specific language governing permissions and limitations
# #    under the License.
#
# # INSTANCE
# from adapters.sql_store import PlanAdapter, ServiceTypeAdapter, PlanServiceTypeAdapter, \
#     ServiceInstanceAdapter as Adapter, ServiceInstanceSQL, ServiceTypeSQL, LastOperationAdapter
# from adapters.store import SQLStore
# from esm.models.service_instance import ServiceInstance
#
# # GENERAL
# import unittest
# from unittest.mock import patch
# from unittest import skipIf
# from orator.exceptions.query import QueryException
# import os
#
#
# # TODO: move to test_store_backends module
#
#
# @skipIf(os.getenv('MYSQL_TESTS', 'NO') != 'YES', "MYSQL_TESTS_TESTS not set in environment variables")
# class TestCaseServiceInstance(unittest.TestCase):
#     def setUp(self):
#         """ PREREQUISITES """
#         PlanAdapter.create_table()
#         ServiceTypeAdapter.create_table()
#         PlanServiceTypeAdapter.create_table()
#         # ManifestAdapter.create_table()
#         self.service = ServiceTypeAdapter.sample_model('instance1')
#         ServiceTypeAdapter.save(self.service)
#
#         Adapter.create_table()
#         self.test_model = Adapter.sample_model('instance1')
#         self.id_name = Adapter.get_id(self.test_model)
#         _, self.result = SQLStore.add_service_instance(self.test_model)
#
#     def tearDown(self):
#         SQLStore.delete_service_instance(Adapter.get_id(self.test_model))
#         ServiceTypeAdapter.delete(self.service.id)
#
#     def test_instance_create_table(self):
#         self.assertTrue(ServiceInstanceSQL.table_exists())
#         with self.assertRaises(QueryException):
#             ServiceInstanceSQL.create_table()
#
#     def test_sample_model(self):
#         self.assertIsInstance(self.test_model, ServiceInstance)
#
#         model_sql = Adapter.find_by_id_name(self.id_name)
#         self.assertIsInstance(model_sql, ServiceInstanceSQL)
#
#         ''' query associated service '''
#         service = model_sql.service
#         self.assertIsInstance(service, ServiceTypeSQL)
#
#         ''' verify relations '''
#         instances = service.instances
#         self.assertGreater(len(instances), 0)
#
#     def test_get_instance_with_instance_id(self):
#         result = SQLStore.get_service_instance(instance_id=self.id_name)
#         self.assertGreater(len(result), 0)
#         self.assertIsInstance(result[0], ServiceInstance)
#
#     def test_adapter_delete(self):
#         with self.assertRaises(Exception):
#             Adapter.delete(id_name='')
#
#     def test_adapter_save_to_update(self):
#         self.test_model.state = LastOperationAdapter.sample_model('instance-updated!')
#         model_sql = Adapter.save(self.test_model)
#         exists = Adapter.exists_in_db(model_sql.id_name)
#         self.assertTrue(exists)
#
#     def test_get_instance_with_id(self):
#         models = SQLStore.get_service_instance(instance_id=self.id_name)
#         self.assertGreater(len(models), 0)
#         self.assertIsInstance(models[0], ServiceInstance)
#
#     @patch.object(Adapter, 'exists_in_db')
#     def test_get_instance_with_id_and_not_found(self, mock_exists_in_db):
#         mock_exists_in_db.return_value = False
#         models = SQLStore.get_service_instance(self.id_name)
#         self.assertEqual(models, [])
#
#     def test_get_instance_with_id_as_none(self):
#         models = SQLStore.get_service_instance(instance_id=None)
#         self.assertNotEqual(models, [])
#
#     def test_instance_created(self):
#         self.assertEqual(self.result, 200, msg='Assert Successful Add')
#         exists = Adapter.exists_in_db(self.id_name)
#         self.assertTrue(exists, msg='Assert Instance exists.')
#         model_sql = Adapter.find_by_id_name(self.id_name)
#         self.assertIsInstance(model_sql, ServiceInstanceSQL)
#
#     def test_instance_deletion(self):
#         _, result = SQLStore.delete_service_instance(self.id_name)
#         self.assertEqual(self.result, 200, msg='Assert Instance Deleted')
#         exists = Adapter.exists_in_db(self.id_name)
#         self.assertFalse(exists, msg='Assert Instance does NOT Exist.')
#         model_sql = Adapter.find_by_id_name(self.id_name)
#         self.assertIsNone(model_sql)
#
#     @patch.object(Adapter, 'exists_in_db')
#     def test_add_instance_existing(self, mock_exists):
#         mock_exists.return_value = True
#         _, result = SQLStore.add_service_instance(self.test_model)
#         self.assertEqual(result, 409, msg='Assert Instance Already Exists')
#
#     def test_delete_instance_nonexistent(self):
#         _, result = SQLStore.delete_service_instance(self.id_name)
#         _, result = SQLStore.delete_service_instance(self.id_name)
#         self.assertEqual(result, 500, msg='Assert Delete Instance Nonexistent')
