# coding: utf-8
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

from __future__ import absolute_import

import os
import inspect

from flask import json

from adapters.store import STORE
from esm.models.manifest import Manifest
from esm.models import ServiceMetadata
from esm.models.plan import Plan
from esm.models.service_type import ServiceType
from . import BaseTestCase

from adapters.log import get_logger

LOG = get_logger(__name__)


class TestCatalogController(BaseTestCase):
    """ CatalogController integration test stubs """

    def setUp(self):
        super().setUp()
        sql_host = os.environ.get('ESM_SQL_HOST', os.environ.get('ET_EDM_MYSQL_HOST', ''))
        if sql_host:
            STORE.set_up()

        self.test_plan = Plan(
            id='testplan', name='testing plan', description='plan for testing',
            metadata=None, free=True, bindable=False
        )
        self.svc_md = ServiceMetadata(
            display_name='thing',
            image_url='http://www.google.com',
            long_description='yeayeayea',
            provider_display_name='god',
            documentation_url='http://elastest.io',
            support_url='http://localhost',
            extras=None
        )
        self.test_service = ServiceType(
            id='test',
            name='test_svc',
            short_name='TS',
            description='this is a test service',
            bindable=False,
            tags=['test', 'tester'],
            metadata=self.svc_md, requires=[],
            plan_updateable=False, plans=[self.test_plan],
            dashboard_client=None)

        self.store = STORE
        self.instance_id = 'this_is_a_test_instance'
        self.binding_id = 'this_is_a_test_instance_binding'

        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/manifests/docker-compose.yml", "r") as mani_file:
            mani = mani_file.read()

        with open(path + '/manifests/test_endpoints.json', 'r') as ep_file:
            ep = ep_file.read()

        self.test_manifest = Manifest(
            id='test', plan_id=self.test_plan.id, service_id=self.test_service.id,
            manifest_type='dummy', manifest_content=mani, endpoints=json.loads(ep)
        )

    def tearDown(self):
        super().tearDown()
        store = STORE
        store.delete_service()
        store.delete_manifest()

    def test_catalog(self):
        """
        Test case for catalog

        Gets services registered within the broker
        """
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/catalog',
                                    method='GET',
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_request_no_version_header(self):
        response = self.client.open('/v2/catalog',
                                    method='GET')
        self.assert400(response, "Response body is : " + response.data.decode('utf-8'))

    def test_register_service(self):
        """
        Test case for register_service

        Registers the service with the catalog.
        """
        response = self._send_svc_reg()
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_double_svc_registration_deny(self):
        response = self._send_svc_reg()
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))
        self.assertEquals(len(STORE.get_service()), 1)

# TODO currently broken with the SQL driver, doesn't not detect that a service descr has changed
    # def test_update_service(self):
    #     """
    #     Test case for udpate register_service
    #
    #     Updates the service with the catalog via PUT.
    #     """
    #     self._send_svc_reg()
    #     self.assertEquals(len(STORE.get_service()), 1)
    #
    #     self.test_service.name = 'this_is_a_fun_funk'
    #     new_test_plan = Plan(
    #         id='newtestplan', name='new testing plan', description='new plan for testing',
    #         metadata=None, free=True, bindable=False
    #     )
    #     self.test_service.plans = [self.test_service.plans[0], new_test_plan]
    #
    #     response = self._send_svc_reg()
    #     self.assert200(response, "Response body is : " + response.data.decode('utf-8'))
    #
    #     svcs = STORE.get_service()
    #     self.assertEquals(len(svcs), 1)
    #     self.assertEquals(len(svcs[0].plans), 2)

    def _send_svc_reg(self):
        headers = [('X_Broker_Api_Version', '2.12')]
        LOG.debug('Sending service registration content of:\n {content}'.format(content=json.dumps(self.test_service)))
        response = self.client.open('/v2/et/catalog',
                                    method='PUT',
                                    data=json.dumps(self.test_service),
                                    content_type='application/json',
                                    headers=headers)
        return response

    def test_store_manifest(self):
        """
        Test case for store_manifest

        takes deployment description of a software service and associates with a service and plan
        """
        response = self._send_svc_reg()
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))
        self.assertEquals(len(STORE.get_service()), 1)

        headers = [('X_Broker_Api_Version', '2.12')]
        LOG.debug('Sending service registration content of:\n {content}'.format(content=json.dumps(self.test_manifest)))
        response = self.client.open('/v2/et/manifest/{manifest_id}'.format(manifest_id=self.test_manifest.id),
                                    method='PUT',
                                    data=json.dumps(self.test_manifest),
                                    content_type='application/json',
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))
        self.assertEquals(len(STORE.get_manifest()), 1)

    def test_update_manifest(self):
        self.test_store_manifest()

        new_test_manifest = Manifest(
            id='test', plan_id=self.test_plan.id, service_id=self.test_service.id,
            manifest_type='dummy', manifest_content=self.test_manifest.manifest_content,
            endpoints=self.test_manifest.endpoints
        )

        headers = [('X_Broker_Api_Version', '2.12')]
        LOG.debug('Sending service registration content of:\n {content}'.format(content=json.dumps(new_test_manifest)))
        response = self.client.open('/v2/et/manifest/{manifest_id}'.format(manifest_id=new_test_manifest.id),
                                    method='PUT',
                                    data=json.dumps(new_test_manifest),
                                    content_type='application/json',
                                    headers=headers)
        self.assertStatus(response, 409)
        self.assertEquals(len(STORE.get_manifest()), 1)

    def test_get_manifest(self):
        """
        Test case for get_manifest

        returns a specific of manifest registered at with the ESM
        """

        self.store.add_service(self.test_service)
        print('Service registration content of:\n {content}'.format(content=json.dumps(self.test_service)))


        headers = [('X_Broker_Api_Version', '2.12')]
        LOG.debug('Sending service registration content of:\n {content}'.format(content=json.dumps(self.test_manifest)))
        response = self.client.open('/v2/et/manifest/{manifest_id}'.format(manifest_id=self.test_manifest.id),
                                    method='PUT',
                                    data=json.dumps(self.test_manifest),
                                    content_type='application/json',
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/et/manifest/{manifest_id}'.format(manifest_id=self.test_manifest.id),
                                    method='GET',
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        # test for nonexistant manifest
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/et/manifest/{manifest_id}'.format(manifest_id='this_is_a_test_instance'),
                                    method='GET',
                                    headers=headers)
        self.assert404(response, "Response body is : " + response.data.decode('utf-8'))

    def test_list_manifests(self):
        """
        Test case for list_manifests

        returns a list of manifests registered at with the ESM
        """

        self.store.add_service(self.test_service)
        print('Service registration content of:\n {content}'.format(content=json.dumps(self.test_service)))


        headers = [('X_Broker_Api_Version', '2.12')]
        LOG.debug('Sending service registration content of:\n {content}'.format(content=json.dumps(self.test_manifest)))
        response = self.client.open('/v2/et/manifest/{manifest_id}'.format(manifest_id=self.test_manifest.id),
                                    method='PUT',
                                    data=json.dumps(self.test_manifest),
                                    content_type='application/json',
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        response = self.client.open('/v2/et/manifest',
                                    method='GET',
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest

    unittest.main()
