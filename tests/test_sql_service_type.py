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
# from esm.models.service_type import ServiceType
#
# from adapters.sql_store import ServiceTypeSQL
# from adapters.sql_store import PlanServiceTypeSQL
# from adapters.sql_store import ServiceTypeAdapter
# from adapters.sql_store import PlanServiceTypeAdapter
# from adapters.sql_store import PlanAdapter
# from adapters.store import SQLStore
#
# from unittest.mock import patch
# from unittest import skipIf
# import unittest
# import os
# from orator.exceptions.query import QueryException
#
# # TODO: move to test_store_backends module
#
#
# @skipIf(os.getenv('MYSQL_TESTS', 'NO') != 'YES', "MYSQL_TESTS not set in environment variables")
# class TestCaseServiceType(unittest.TestCase):
#     def setUp(self):
#         self.test_model = ServiceTypeAdapter.sample_model('service1')
#         ServiceTypeAdapter.create_table()
#         PlanAdapter.create_table()
#         PlanServiceTypeAdapter.create_table()
#         _, self.result = SQLStore.add_service(self.test_model)
#
#     def tearDown(self):
#         SQLStore.delete_service(self.test_model.id)
#
#     def test_plan_service_type_create_table(self):
#         self.assertTrue(PlanServiceTypeSQL.table_exists())
#         with self.assertRaises(QueryException):
#             PlanServiceTypeSQL.create_table()
#
#     def test_service_type_create_table(self):
#         self.assertTrue(ServiceTypeSQL.table_exists())
#         with self.assertRaises(QueryException):
#             ServiceTypeSQL.create_table()
#
#     def test_sample_model_with_plans(self):
#         self.assertIsInstance(self.test_model, ServiceType)
#
#         model_sql = ServiceTypeAdapter.find_by_id_name(self.test_model.id)
#         self.assertIsInstance(model_sql, ServiceTypeSQL)
#         self.assertFalse(model_sql.plans.is_empty())
#
#         plans = PlanAdapter.plans_from_service_sql(model_sql)
#         self.assertGreater(len(plans), 1)
#
#         model = ServiceTypeAdapter.model_sql_to_model(model_sql)
#         self.assertGreater(len(model.plans), 1)
#
#     def test_adapter_delete(self):
#         with self.assertRaises(Exception):
#             ServiceTypeAdapter.delete(id_name='')
#
#     def test_adapter_save_to_update(self):
#         self.test_model.name = 'new-name'
#         model_sql = ServiceTypeAdapter.save(self.test_model)
#         exists = ServiceTypeAdapter.exists_in_db(model_sql.id_name)
#         self.assertTrue(exists)
#
#     def test_get_service_with_id(self):
#         services = SQLStore.get_service(service_id=self.test_model.id)
#         self.assertGreater(len(services), 0)
#         self.assertIsInstance(services[0], ServiceType)
#
#     @patch.object(ServiceTypeAdapter, 'exists_in_db')
#     def test_get_service_with_id_and_not_found(self, mock_exists_in_db):
#         mock_exists_in_db.return_value = False
#         services = SQLStore.get_service(self.test_model.id)
#         self.assertEqual(services, [])
#
#     def test_get_service_with_id_as_none(self):
#         services = SQLStore.get_service(service_id=None)
#         self.assertNotEqual(services, [])
#
#     def test_service_created(self):
#         self.assertEqual(self.result, 200, msg='Assert Successful Add')
#         exists = ServiceTypeAdapter.exists_in_db(self.test_model.id)
#         self.assertTrue(exists, msg='Assert service service exists.')
#         service_sql = ServiceTypeAdapter.find_by_id_name(self.test_model.id)
#         self.assertIsInstance(service_sql, ServiceTypeSQL)
#
#     def test_service_deletion(self):
#         _, result = SQLStore.delete_service(self.test_model.id)
#         self.assertEqual(self.result, 200, msg='Assert Service Deleted')
#         exists = ServiceTypeAdapter.exists_in_db(self.test_model.id)
#         self.assertFalse(exists, msg='Assert service does NOT Exist.')
#         service_sql = ServiceTypeAdapter.find_by_id_name(self.test_model.id)
#         self.assertIsNone(service_sql)
#
#     @patch.object(ServiceTypeAdapter, 'exists_in_db')
#     def test_add_service_existing(self, mock_exists):
#         mock_exists.return_value = True
#         _, result = SQLStore.add_service(self.test_model)
#         self.assertEqual(result, 409, msg='Assert Service Already Exists')
#
#     def test_delete_service_nonexistent(self):
#         _, result = SQLStore.delete_service(self.test_model.id)
#         _, result = SQLStore.delete_service(self.test_model.id)
#         self.assertEqual(result, 500, msg='Assert Delete Service Nonexistent')
#
#     def test_delete_all(self):
#         _, result = SQLStore.delete_service(service_id=None)
#         self.assertEqual(self.result, 200, msg='Assert Service Delete w/ \'None\'')
