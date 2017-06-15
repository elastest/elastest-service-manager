# coding: utf-8

from __future__ import absolute_import

from esm.models.catalog_service import CatalogService
from esm.models.catalog_services import CatalogServices
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestCatalogController(BaseTestCase):
    """ CatalogController integration test stubs """

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
        service = CatalogService()
        response = self.client.open('/v2-et/catalog',
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
