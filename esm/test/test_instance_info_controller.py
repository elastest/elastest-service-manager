# coding: utf-8

from __future__ import absolute_import

from esm.models.catalog_service import CatalogService
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestInstanceInfoController(BaseTestCase):
    """ InstanceInfoController integration test stubs """

    def test_instance_info(self):
        """
        Test case for instance_info

        Returns information about the service instance.
        """
        response = self.client.open('/v2-et/service_instances/{instance_id}'.format(instance_id='instance_id_example'),
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
