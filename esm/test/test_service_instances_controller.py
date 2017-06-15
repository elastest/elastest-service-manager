# coding: utf-8

from __future__ import absolute_import

from esm.models.binding import Binding
from esm.models.binding_response import BindingResponse
from esm.models.dashboard_url import DashboardUrl
from esm.models.empty import Empty
from esm.models.error import Error
from esm.models.service import Service
from esm.models.service_plan import ServicePlan
from esm.models.update_operation import UpdateOperation
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestServiceInstancesController(BaseTestCase):
    """ ServiceInstancesController integration test stubs """

    def test_create_service_instance(self):
        """
        Test case for create_service_instance

        Provisions a service instance
        """
        service = Service()
        query_string = [('accept_incomplete', 'accept_incomplete_example')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id='instance_id_example'),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_deprovision_service_instance(self):
        """
        Test case for deprovision_service_instance

        Deprovisions a service instance.
        """
        query_string = [('service_id', 'service_id_example'),
                        ('plan_id', 'plan_id_example'),
                        ('accept_incomplete', 'accept_incomplete_example')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id='instance_id_example'),
                                    method='DELETE',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_service_bind(self):
        """
        Test case for service_bind

        Binds to a service
        """
        binding = Binding()
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}'.format(instance_id='instance_id_example', binding_id='binding_id_example'),
                                    method='PUT',
                                    data=json.dumps(binding),
                                    content_type='application/json')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_service_unbind(self):
        """
        Test case for service_unbind

        Unbinds a service
        """
        query_string = [('service_id', 'service_id_example'),
                        ('plan_id', 'plan_id_example')]
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}'.format(instance_id='instance_id_example', binding_id='binding_id_example'),
                                    method='DELETE',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_update_service_instance(self):
        """
        Test case for update_service_instance

        Updating a Service Instance
        """
        plan = ServicePlan()
        query_string = [('accept_incomplete', 'accept_incomplete_example')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id='instance_id_example'),
                                    method='PATCH',
                                    data=json.dumps(plan),
                                    content_type='application/json',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
