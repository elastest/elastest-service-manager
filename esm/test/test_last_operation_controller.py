# coding: utf-8

from __future__ import absolute_import

from esm.models.last_operation import LastOperation
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestLastOperationController(BaseTestCase):
    """ LastOperationController integration test stubs """

    def test_last_operation_status(self):
        """
        Test case for last_operation_status

        Gets the current state of the last operation upon the specified resource.
        """
        query_string = [('service_id', 'service_id_example'),
                        ('plan_id', 'plan_id_example'),
                        ('operation', 'operation_example')]
        response = self.client.open('/v2/service_instances/{instance_id}/last_operation'.format(instance_id='instance_id_example'),
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
