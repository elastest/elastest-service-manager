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

from unittest import skipIf
import unittest
import os

from unittest.mock import patch
from adapters.sql_store import ManifestAdapter

if os.getenv('ESM_SQL_HOST', 'NO') == 'YES':
    # MANIFEST
    from esm.models.manifest import Manifest
    from adapters.sql_store import ManifestSQL
    # SERVICE
    from adapters.sql_store import ServiceTypeSQL
    from adapters.sql_store import PlanServiceTypeAdapter
    from adapters.sql_store import ServiceTypeAdapter
    # PLAN
    from adapters.sql_store import PlanAdapter
    # GENERICS
    from adapters.store import SQLStore
    from orator.exceptions.query import QueryException


# TODO: move to test_store_backends module


@skipIf(os.getenv('MYSQL_TESTS', 'NO') != 'YES', "MYSQL_TESTS not set in environment variables")
class TestCaseManifest(unittest.TestCase):

    def setUp(self):
        """PREREQUISITES"""
        PlanAdapter.create_table()
        ServiceTypeAdapter.create_table()
        PlanServiceTypeAdapter.create_table()
        self.service = ServiceTypeAdapter.sample_model('manifest1')
        ServiceTypeAdapter.save(self.service)

        ManifestAdapter.create_table()
        self.test_model = ManifestAdapter.sample_model('manifest1')
        _, self.result = SQLStore.add_manifest(self.test_model)

    def tearDown(self):
        SQLStore.delete_manifest(self.test_model.id)
        ServiceTypeAdapter.delete(self.service.id)

    def test_manifest_create_table(self):
        self.assertTrue(ManifestSQL.table_exists())
        with self.assertRaises(QueryException):
            ManifestSQL.create_table()

    def test_sample_model_with_plans(self):
        self.assertIsInstance(self.test_model, Manifest)

        model_sql = ManifestAdapter.find_by_id_name(self.test_model.id)
        self.assertIsInstance(model_sql, ManifestSQL)

        ''' query associated service '''
        service = model_sql.service
        self.assertIsInstance(service, ServiceTypeSQL)

        ''' verify relations '''
        plans = service.plans
        plan = model_sql.plan
        self.assertTrue(plan in plans)

        ''' manifest also deleted '''
        PlanAdapter.delete(plan.id_name)
        self.assertFalse(ManifestAdapter.exists_in_db(model_sql.id_name))

        ''' service updated (has to be re-query-ed) '''
        ''' this is not correct! >> service = model_sql.service '''
        service = ServiceTypeAdapter.find_by_id_name(service.id_name)
        plans = service.plans
        ''' verify plans reduced '''
        self.assertEqual(len(plans), 1)
        ''' verify service has no manifest now '''
        self.assertTrue(service.manifests.is_empty())

    def test_adapter_delete(self):
        with self.assertRaises(Exception):
            ManifestAdapter.delete(id_name='')

    def test_adapter_save_to_update(self):
        self.test_model.name = 'new-name'
        model_sql = ManifestAdapter.save(self.test_model)
        exists = ManifestAdapter.exists_in_db(model_sql.id_name)
        self.assertTrue(exists)

    def test_get_manifest_with_id(self):
        manifests = SQLStore.get_manifest(manifest_id=self.test_model.id)
        self.assertGreater(len(manifests), 0)
        self.assertIsInstance(manifests[0], Manifest)

    def test_get_manifest_with_manifest_id_and_plan_id(self):
        with self.assertRaises(Exception):
            SQLStore.get_manifest(manifest_id=self.test_model.id, plan_id=self.test_model.plan_id)

    def test_get_manifest_with_manifest_id(self):
        result = SQLStore.get_manifest(manifest_id=self.test_model.id, plan_id=None)
        self.assertGreater(len(result), 0)
        self.assertIsInstance(result[0], Manifest)

    # TODO(franco) fixme this is borked!
    # def test_get_manifest_with_plan_id(self):
    #     result = SQLStore.get_manifest(manifest_id=None, plan_id=self.test_model.plan_id)
    #     self.assertGreater(len(result), 0)
    #     self.assertIsInstance(result[0], Manifest)

    @patch.object(ManifestAdapter, 'exists_in_db')
    def test_get_manifest_with_id_and_not_found(self, mock_exists_in_db):
        mock_exists_in_db.return_value = False
        manifests = SQLStore.get_manifest(self.test_model.id)
        self.assertEqual(manifests, [])

    # TODO(franco) fixme this is borked
    # def test_get_manifest_with_id_as_none(self):
    #     manifests = SQLStore.get_manifest(manifest_id=None)
    #     self.assertNotEqual(manifests, [])

    def test_manifest_created(self):
        self.assertEqual(self.result, 200, msg='Assert Successful Add')
        exists = ManifestAdapter.exists_in_db(self.test_model.id)
        self.assertTrue(exists, msg='Assert manifest exists.')
        manifest_sql = ManifestAdapter.find_by_id_name(self.test_model.id)
        self.assertIsInstance(manifest_sql, ManifestSQL)

    def test_manifest_deletion(self):
        _, result = SQLStore.delete_manifest(self.test_model.id)
        self.assertEqual(self.result, 200, msg='Assert Manifest Deleted')
        exists = ManifestAdapter.exists_in_db(self.test_model.id)
        self.assertFalse(exists, msg='Assert manifest does NOT Exist.')
        manifest_sql = ManifestAdapter.find_by_id_name(self.test_model.id)
        self.assertIsNone(manifest_sql)

    @patch.object(ManifestAdapter, 'exists_in_db')
    def test_add_manifest_existing(self, mock_exists):
        mock_exists.return_value = True
        _, result = SQLStore.add_manifest(self.test_model)
        self.assertEqual(result, 409, msg='Assert Manifest Already Exists')

    def test_delete_manifest_nonexistent(self):
        _, result = SQLStore.delete_manifest(self.test_model.id)
        _, result = SQLStore.delete_manifest(self.test_model.id)
        self.assertEqual(result, 500, msg='Assert Delete Manifest Nonexistent')

    # TODO(franco) delete all implementation must be changed.
        # current: truncate/drop table
        # preferred: loop over entities and delete manually.

    # def test_delete_manifest_none(self):
    #     _, result = SQLStore.delete_manifest(manifest_id=None)
    #     self.assertEqual(self.result, 200, msg='Assert Manifest Delete w/ \'None\'')
