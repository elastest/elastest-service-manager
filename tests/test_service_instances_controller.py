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
import os
import unittest

from flask import json

from adapters.store import STORE
from esm.models.manifest import Manifest
from esm.models.plan import Plan
from esm.models.service_type import ServiceType
from esm.models.binding_request import BindingRequest
from esm.models.service_request import ServiceRequest
from esm.models.update_request import UpdateRequest

from . import BaseTestCase


from adapters.log import get_logger

LOG = get_logger(__name__)
MANIFEST = os.environ.get("TEST_MANIFEST_CONTENT", "/manifests/docker-compose.yml")


class TestServiceInstancesController(BaseTestCase):
    """ ServiceInstancesController integration test stubs """

    def setUp(self):
        super().setUp()
        sql_host = os.environ.get('ESM_SQL_HOST', os.environ.get('ET_EDM_MYSQL_HOST', ''))
        if sql_host:
            STORE.set_up()

        self.store = STORE
        if len(self.store.get_service_instance()) > 0:
            raise Exception('This shouldnt happen - the store should be empty on each run!')

        self.instance_id = 'this_is_a_test_instance'
        self.binding_id = 'this_is_a_test_instance_binding'

        self.test_plan = Plan(
            id='testplan', name='testing plan', description='plan for testing',
            metadata=None, free=True, bindable=False
        )

        self.test_service = ServiceType(
            id='test-svc', name='test_svc',
            description='this is a test service',
            bindable=True,
            tags=['test', 'tester'],
            metadata=None, requires=[],
            plan_updateable=False, plans=[self.test_plan],
            dashboard_client=None)

        self.store.add_service(self.test_service)
        print('Service registration content of:\n {content}'.format(content=json.dumps(self.test_service)))

        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        with open(path + MANIFEST, "r") as mani_file:
            mani = mani_file.read()

        with open(path + '/manifests/test_endpoints.json', 'r') as ep_file:
            ep = ep_file.read()

        if os.getenv('DOCKER_TESTS', 'NO') == 'YES':
            m_type = 'docker-compose'
        else:
            m_type = 'dummy'

        self.test_manifest = Manifest(
            id='test-mani', plan_id=self.test_plan.id, service_id=self.test_service.id,
            manifest_type=m_type, manifest_content=mani, endpoints=json.loads(ep)
        )
        self.store.add_manifest(self.test_manifest)
        print('Manifest registration content of:\n {content}'.format(content=json.dumps(self.test_manifest)))

        self.response = self._send_service_request()
        self._assert200(self.response)

    def _assert200(self, response):
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def tearDown(self):
        # self.store.delete_service()
        # self.store.delete_manifest()
        # self.store.delete_service_instance()
        # self.store.delete_last_operation()
        response = self._delete_service_instance()
        self._assert200(response)

    def _send_service_request(self, headers=[('X_Broker_Api_Version', '2.12')], params={}):
        service = ServiceRequest(service_id=self.test_service.id, plan_id=self.test_plan.id,
                                 organization_guid='org', space_guid='space', parameters=params)
        query_string = [('accept_incomplete', False)]
        print('Sending service instantiation content of:\n {content}'.format(content=json.dumps(service)))
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='PUT',
                                    data=json.dumps(service),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        return response

    def _delete_service_instance(self):
        query_string = [('service_id', 'srv'),
                        ('plan_id', 'plan'),
                        ('accept_incomplete', False)]
        headers = [('X_Broker_Api_Version', '2.12')]

        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='DELETE',
                                    query_string=query_string,
                                    headers=headers)
        return response

    def test_request_no_version_header(self):
        response = self._send_service_request(headers=[])
        self.assert400(response, "Response body is : " + response.data.decode('utf-8'))

    def test_create_service_instance(self):
        """
        Test case for create_service_instance

        Provisions a service instance
        """
        self._assert200(self.response)
        self.assertEquals(len(STORE.get_service_instance()), 1)

    def test_create_instance_with_same_id(self):
        # send the same request twice
        response = self._send_service_request()
        self.assertEqual(response.status_code, 409)

    def test_create_instance_with_nonexistant_plan(self):
        self._delete_service_instance()
        service = ServiceRequest(service_id=self.test_service.id, plan_id='WRONG_ONE',
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
        self.assert404(response, "Response body is : " + response.data.decode('utf-8'))
        self._send_service_request()

    def test_create_service_instance_with_params(self):
        """
        Test case for create_service_instance

        Provisions a service instance
        """
        self._delete_service_instance()

        params = dict()
        params['ET_ESM_API'] = 'http://esm:37005/'
        params['pop_name'] = 'just_a_test'

        # params['all'] = dict()
        # params['svc1'] = dict()  # should raise a 4xx error as it doesnt exist in manifest
        # params['elastest-eus'] = dict()
        # params['all']['TEST-ALL'] = 'value1'
        # params['svc1']['TEST1'] = 'value'  # should raise a 4xx error
        # params['elastest-eus']['TEST2'] = 'value1'
        # params['elastest-eus']['ET_ESM_API'] = 'http://esm:37005/'

        response = self._send_service_request(params=params)
        self._assert200(response)

        import time
        time.sleep(3)

        # should do a get on the instance and verify that the params are set.
        # get info from the instance
        # get info from the instance
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/et/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='GET', headers=headers)
        self._assert200(response)

        def _check_key(key_name, info):
            res = False
            for x in info:
                if key_name in x:
                    res = True
            return res

        self.assertTrue(_check_key('ET_ESM_API', response.json['context']))

    def test_deprovision_service_instance(self):
        """
        Test case for deprovision_service_instance

        Deprovisions a service instance.
        """

        response = self._delete_service_instance()
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))
        self._send_service_request()

    def test_all_instance_info(self):
        """
        Test case for all_instance_info

        Returns information about the service instance.
        """

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

        # get info from the instance
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/et/service_instances/{instance_id}'.format(instance_id=self.instance_id),
                                    method='GET', headers=headers)

        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

        # let's ensure that IP addresses are always given (key to the TORM)
        ips = [v for k, v in json.loads(response.data)['context'].items() if k.endswith('_Ip')]
        # self.assertGreater(len(ips), 0)  # TODO reenable me please!

        # check that 404 is returned if invalid instance is requested
        response = self.client.open('/v2/et/service_instances/{instance_id}'.format(instance_id='I_DO_NOT_EXIST'),
                                    method='GET', headers=headers)
        self.assert404(response, "Response body is : " + response.data.decode('utf-8'))

    def test_last_operation_status(self):
        """
        Test case for last_operation_status

        Gets the current state of the last operation upon the specified resource.
        """
        query_string = [('service_id', self.test_service.id),  # 'service_id_example'
                        ('plan_id', self.test_plan.id),  # 'plan_id_example'
                        ('operation', 'operation_example')]  # not used
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}/last_operation'.format(
            instance_id=self.instance_id),
                                    method='GET',
                                    query_string=query_string, headers=headers)
        self.assert200(response, "Response body is : " + response.data.decode('utf-8'))

    def test_service_bind_unbind(self):
        """
        Test case for service_bind, service_unbind

        Bind & Unbinds a service
        """
        LOG.warn('starting binding test case... asserting...')

        self.assert200(self.response, "Response body is : " + self.response.data.decode('utf-8'))

        # bind to the service
        LOG.warn('binding...')
        binding = BindingRequest(service_id=self.test_service.id, plan_id=self.test_plan.id)
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}'.format(
            instance_id=self.instance_id, binding_id=self.binding_id),
            method='PUT',
            data=json.dumps(binding),
            content_type='application/json',
            headers=headers)
        self.assertStatus(response, 200, "Response body is : " + response.data.decode('utf-8'))

        # unbind the service
        LOG.warn('un..binding.....')
        # binding = BindingRequest(service_id=self.test_service.id, plan_id=self.test_plan.id)
        headers = [('X_Broker_Api_Version', '2.12')]
        # params = {'service_id': self.test_service.id, 'plan_id': self.test_plan.id}
        response = self.client.open('/v2/service_instances/{instance_id}/service_bindings/{binding_id}?'
                                    'service_id={sid}&plan_id={pid}'.format(
                                        instance_id=self.instance_id, binding_id=self.binding_id,
                                        sid=self.test_service.id, pid=self.test_plan.id),
            method='DELETE',
            content_type='application/json',
            headers=headers
        )
        self.assertStatus(response, 200, "Response body is : " + response.data.decode('utf-8'))

    def test_update_service_instance(self):
        """
        Test case for update_service_instance

        Updating a Service Instance
        """
        plan = UpdateRequest(service_id='svc')
        query_string = [('accept_incomplete', False)]
        headers = [('X_Broker_Api_Version', '2.12')]
        response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id='svc_id'),
                                    method='PATCH',
                                    data=json.dumps(plan),
                                    content_type='application/json',
                                    query_string=query_string,
                                    headers=headers)
        self.assertStatus(response, 501, "Response body is : " + response.data.decode('utf-8'))


# TODO new test

    # test attempted deletion of non-existant instance
    # response = self.client.open('/v2/service_instances/{instance_id}'.format(instance_id='I_DO_NOT_EXIST'),
    #                             method='DELETE',
    #                             query_string=query_string,
    #                             headers=headers)
    # self.assert404(response, "Response body is : " + response.data.decode('utf-8'))

if __name__ == '__main__':
    import unittest
    unittest.main()
