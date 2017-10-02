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

import inspect

import adapters.log
import os
from adapters.datasource import STORE
from esm.models.manifest import Manifest
from esm.models.plan import Plan
from esm.models.service_type import ServiceType
from esm.models.binding_request import BindingRequest
from esm.models.service_request import ServiceRequest
from flask import json

from esm.models.update_request import UpdateRequest
from . import BaseTestCase

# from esm.models.binding_response import BindingResponse
# from esm.models.empty import Empty
# from esm.models.error import Error
# from esm.models.last_operation import LastOperation
# from esm.models.service_response import ServiceResponse
# from esm.models.update_operation_response import UpdateOperationResponse
# from six import BytesIO


LOG = adapters.log.get_logger(name=__name__)


class TestServiceInstancesController(BaseTestCase):
    """ ServiceInstancesController integration test stubs """

    def setUp(self):
        super().setUp()

        self.store = STORE
        self.instance_id = 'this_is_a_test_instance'

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

        self.store.add_service(self.test_service)
        print('Service registration content of:\n {content}'.format(content=json.dumps(self.test_service)))

        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + "/manifests/docker-compose.yml", "r") as mani_file:
            mani = mani_file.read()

        with open(path + '/manifests/test_endpoints.json', 'r') as ep_file:
            ep = ep_file.read()

        self.test_manifest = Manifest(
            id='test-mani', plan_id=self.test_plan.id, service_id=self.test_service.id,
            manifest_type='dummy', manifest_content=mani, endpoints=json.loads(ep)
        )

        self.store.add_manifest(self.test_manifest)
        print('Manifest registration content of:\n {content}'.format(content=json.dumps(self.test_manifest)))

    def tearDown(self):
        self.store.delete_service()
        self.store.delete_manifest()
        self.store.delete_service_instance()
        self.store.delete_last_operation()

    def test_create_service_instance(self):
        """
        Test case for create_service_instance

        Provisions a service instance
        """
        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        headers = [('X_Broker_Api_Version', '2.12')]
        print('Sending service instantiation content of:\n {content}'.format(content=json.dumps(service)))
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_create_service_instance_with_params(self):
        """
        Test case for create_service_instance

        Provisions a service instance
        """

        params = dict()
        params['TEST'] = 'value'
        params['TEST1'] = 'value1'

        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space', parameters=params)

        query_string = [('accept_incomplete', False)]
        headers = [('X_Broker_Api_Version', '2.12')]
        print('Sending service instantiation content of:\n {content}'.format(content=json.dumps(service)))
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_deprovision_service_instance(self):
        """
        Test case for deprovision_service_instance

        Deprovisions a service instance.
        """

        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        query_string = [('service_id', 'srv'),
                        ('plan_id', 'plan'),
                        ('accept_incomplete', True)]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='DELETE',
                                    query_string=query_string,
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_all_instance_info(self):
        """
        Test case for all_instance_info

        Returns information about the service instance.
        """

        # create the instance we want to get info from
        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        # get info from the instance
        headers = [('X_Broker_Api_Version', '2.12')]

        response = self.client.open('/v2/et/service_instances',
                                    method='GET',
                                    headers=headers)
        # should be a json array of size 1
        resp_body = response.data.decode('utf-8')
        self.assert200(response, "Response body is : " + resp_body)
        self.assertTrue(len(json.loads(resp_body)) == 1)

    def test_instance_info(self):
        """
        Test case for instance_info

        Returns information about the service instance.
        """

        # create the instance we want to get info from
        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space')
        query_string = [('accept_incomplete', False)]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        # get info from the instance
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/et/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='GET', headers=headers)
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
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        query_string = [('service_id', 'service_id_example'),
                        ('plan_id', 'plan_id_example'),
                        ('operation', 'operation_example')]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}/last_operation'.format(
            instance_id=self.instance_id),
                                    method='GET',
                                    query_string=query_string, headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_service_bind(self):
        """
        Test case for service_bind

        Binds to a service
        """
        binding = BindingRequest(service_id='svc', plan_id='plan')
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}'.format(
            instance_id='svc_id', binding_id='binding_id_example'),
                                    method='PUT',
                                    data=json.dumps(binding),
                                    content_type='application/json',
                                    headers=headers)
        self.assertStatus(response, 501, "Response body is : " + response.data.decode('utf-8'))

    def test_service_unbind(self):
        """
        Test case for service_unbind

        Unbinds a service
        """
        query_string = [('service_id', 'service_id_example'),
                        ('plan_id', 'plan_id_example')]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}'.format(
            instance_id='svc_id', binding_id='binding_id_example'),
                                    method='DELETE',
                                    query_string=query_string,
                                    headers=headers)
        self.assertStatus(response, 501, "Response body is : " + response.data.decode('utf-8'))

    def test_update_service_instance(self):
        """
        Test case for update_service_instance

        Updating a Service Instance
        """
        plan = UpdateRequest(service_id='svc')
        query_string = [('accept_incomplete', True)]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id='svc_id'),
                                    method='PATCH',
                                    data=json.dumps(plan),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assertStatus(response, 501, "Response body is : " + response.data.decode('utf-8'))


if __name__ == '__main__':
    import unittest
    unittest.main()
    # import nose
    # nose.main()
