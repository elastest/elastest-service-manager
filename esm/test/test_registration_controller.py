# coding: utf-8

from __future__ import absolute_import

from esm.models.catalog_service import CatalogService
from esm.models.catalog_services import CatalogServices
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestRegistrationController(BaseTestCase):
    """ RegistrationController integration test stubs """

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
