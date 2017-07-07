# coding: utf-8

from __future__ import absolute_import
import inspect, os

from esm.models.binding_request import BindingRequest
from esm.models.binding_response import BindingResponse
from esm.models.empty import Empty
from esm.models.error import Error
from esm.models.last_operation import LastOperation
from esm.models.service_request import ServiceRequest
from esm.models.service_response import ServiceResponse
from esm.models import ServiceType
from esm.models import Plan
from esm.models import Manifest
from esm.models.update_operation_response import UpdateOperationResponse
from esm.models.update_request import UpdateRequest
from . import BaseTestCase
from six import BytesIO
from flask import json


class TestServiceInstancesController(BaseTestCase):
    """ ServiceInstancesController integration test stubs """

    def tearDown(self):
        super().tearDown()
        from pymongo import MongoClient
        CLIENT = MongoClient('localhost', 27017)
        CLIENT.esm.services.delete_many({})
        CLIENT.esm.manifests.delete_many({})

    def setUp(self):
        super().setUp()

        self.instance_id = 'this_is_a_test_instance'

        from pymongo import MongoClient
        CLIENT = MongoClient('localhost', 27017)

        self.test_plan = Plan(
            id='testplan', name='testing plan', description='plan for testing',
            metadata=None, free=True, bindable=False
        )

        self.test_service = ServiceType(
            id='test-svc', name='test_svc',
            description='this is a test service',
            bindable=False,
            tags=['test', 'tester'],
            metadata=None, requires=[],
            plan_updateable=False, plans=[self.test_plan],
            dashboard_client=None)

        CLIENT.esm.services.insert_one(self.test_service.to_dict())

        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/docker-compose.yml", "r") as mani_file:
            mani = mani_file.read().replace('\n', '</br>')

        self.test_manifest = Manifest(
            id='test-mani', plan_id=self.test_plan.id, service_id=self.test_service.id,
            manifest_type='docker-compose', manifest_content=mani)

        # manifest_type should be set to test for tests and therefore select the dummydriver

        CLIENT.esm.manifests.insert_one(self.test_manifest.to_dict())

    def test_create_service_instance(self):
        """
        Test case for create_service_instance

        Provisions a service instance
        """
        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
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

        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        query_string = [('service_id', 'srv'),
                        ('plan_id', 'plan'),
                        ('accept_incomplete', True)]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='DELETE',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_instance_info(self):
        """
        Test case for instance_info

        Returns information about the service instance.
        """

        # create the instance we want to get info from
        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        # get info from the instance
        response = self.client.open('/v2/et/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='GET')
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_last_operation_status(self):
        """
        Test case for last_operation_status

        Gets the current state of the last operation upon the specified resource.
        """

        # create the instance we want to get info from
        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


        query_string = [('service_id', 'service_id_example'),
                        ('plan_id', 'plan_id_example'),
                        ('operation', 'operation_example')]
        response = self.client.open('/v2/service_instances/{instance_id}/last_operation'.format(instance_id=self.instance_id),
                                    method='GET',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_service_bind(self):
        """
        Test case for service_bind

        Binds to a service
        """
        binding = BindingRequest(service_id='svc', plan_id='plan')
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}'.format(
            instance_id='svc_id', binding_id='binding_id_example'),
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
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}'.format(
            instance_id='svc_id', binding_id='binding_id_example'),
                                    method='DELETE',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_update_service_instance(self):
        """
        Test case for update_service_instance

        Updating a Service Instance
        """
        plan = UpdateRequest(service_id='svc')
        query_string = [('accept_incomplete', True)]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id='svc_id'),
                                    method='PATCH',
                                    data=json.dumps(plan),
                                    content_type='application/json',
                                    query_string=query_string)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
