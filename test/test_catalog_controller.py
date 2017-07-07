# coding: utf-8

from __future__ import absolute_import

from esm.models.catalog import Catalog
from esm.models.empty import Empty
from esm.models.error import Error
from esm.models.plan import Plan
from esm.models.manifest import Manifest
from esm.models.service_type import ServiceType
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestCatalogController(BaseTestCase):
    """ CatalogController integration test stubs """

    def tearDown(self):
        super().tearDown()
        from pymongo import MongoClient
        CLIENT = MongoClient('localhost', 27017)
        result = CLIENT.esm.services.delete_many({})
        result = CLIENT.esm.manifests.delete_many({})

    def setUp(self):
        super().setUp()
        self.test_plan = Plan(
            id='testplan', name='testing plan', description='plan for testing',
            metadata=None, free=True, bindable=False
        )
        self.test_service = ServiceType(
            id='test', name='test_svc',
            description='this is a test service',
            bindable=False,
            tags=['test', 'tester'],
            metadata=None, requires=[],
            plan_updateable=False, plans=[self.test_plan],
            dashboard_client=None)

        self.test_manifest = Manifest(
            id='test', plan_id=self.test_plan.id, service_id=self.test_service.id,
            manifest_type='docker', manifest_content=''
        )

    def test_catalog(self):
        """
        Test case for catalog

        Gets services registered within the broker
        """
        response = self.client.open('/v2/catalog',
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_register_service(self):
        """
        Test case for register_service

        Registers the service with the catalog.
        """

        response = self.client.open('/v2/et/catalog',
                                    method='PUT',
                                    data=json.dumps(self.test_service),
                                    content_type='application/json')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_store_manifest(self):
        """
        Test case for store_manifest

        takes deployment description of a software service and associates with a service and plan
        """

        response = self.client.open('/v2/et/catalog',
                                    method='PUT',
                                    data=json.dumps(self.test_service),
                                    content_type='application/json')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        response = self.client.open('/v2/et/manifest/{manifest_id}'.format(manifest_id=self.test_manifest.id),
                                    method='PUT',
                                    data=json.dumps(self.test_manifest),
                                    content_type='application/json')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
