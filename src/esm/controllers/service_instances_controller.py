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

import connexion

import config
from adapters.generic import AsychExe
from adapters.store import STORE
from adapters.resources import RM
from adapters.auth import AUTH
from esm.controllers import _version_ok
from esm.controllers.tasks import CreateInstance, DeleteInstance, RetrieveInstance, \
    RetrieveAllInstances, RetrieveInstanceLastOp, BindInstance, UnbindInstance, \
    UpdateInstance, MeasureInstance

from esm.models.binding_response import BindingResponse
from esm.models.empty import Empty
from esm.models.last_operation import LastOperation
from esm.models.service_instance import ServiceInstance
from esm.models.service_request import ServiceRequest
from esm.models.service_response import ServiceResponse
from esm.models.update_operation_response import UpdateOperationResponse
from esm.models.update_request import UpdateRequest

from adapters.log import get_logger

LOG = get_logger(__name__)


def create_service_instance(instance_id, service, accept_incomplete=False):
    """
    Provisions a service instance
    When the broker receives a provision request from a client, it should synchronously take whatever action is
    necessary to create a new service resource for the developer. The result of provisioning varies by service
    type, although there are a few common actions that work for many services. Supports asynchronous operations.&#39;
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for
    future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39;
    :type instance_id: str
    :param service: Service information.
    :type service: dict | bytes
    :param accept_incomplete: Indicates that the client is supporting asynchronous operations
    :type accept_incomplete: bool

    :rtype: ServiceResponse
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        if connexion.request.is_json:
            service_inst_req = ServiceRequest.from_dict(connexion.request.get_json())
        else:
            return "Supplied body content is not or is mal-formed JSON", 400

        entity = {'entity_id': instance_id, 'entity_req': service_inst_req, 'entity_res': None}
        context = {'STORE': STORE, 'RM': RM}

        if accept_incomplete:
            AsychExe([CreateInstance(entity, context)]).start()
            return 'accepted', 201
        else:
            # we have the result of the operation in entity, good/bad status in context
            entity, context = CreateInstance(entity, context).start()
            if config.esm_measure_insts == 'YES':
                # entity, context = #
                MeasureInstance(entity, context).start()
            # Response is ServiceResponse not a service instance
            return entity['entity_res'], context['status'][1]


def deprovision_service_instance(instance_id, service_id, plan_id, accept_incomplete=False):
    """
    Deprovisions a service instance.
    &#39;When a broker receives a deprovision request from a client, it should delete any resources it
    created during the provision. Usually this means that all resources are immediately reclaimed for
    future provisions.&#39;
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used
    for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39;
    :type instance_id: str
    :param service_id: service ID to be deprovisioned
    :type service_id: str
    :param plan_id: plan ID of the service to be deprovisioned
    :type plan_id: str
    :param accept_incomplete: Indicates that the client is supporting asynchronous operations
    :type accept_incomplete: bool

    :rtype: UpdateOperationResponse
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        entity = {'entity_id': instance_id, 'entity_req': {'service_id': service_id, 'plan_id': plan_id},
                  'entity_res': None}
        context = {'STORE': STORE, 'RM': RM}

        # XXX if there's bindings remove first?
        if accept_incomplete:
            AsychExe([DeleteInstance(entity, context)]).start()
            return 'accepted', 201
        else:
            entity, context = DeleteInstance(entity, context).start()
            # response is UpdateOperationResponse
            return entity['entity_res'], context['status'][1]


def instance_info(instance_id):
    """
    Returns information about the service instance.
    Returns information about the service instance. This is a simple read operation against the broker database and
    is provided as a developer/consumer convienence.
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used
    for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39;
    :type instance_id: str

    :rtype: ServiceInstance
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        entity = {'entity_id': instance_id, 'entity_req': {}, 'entity_res': None}
        context = {'STORE': STORE, 'RM': RM}

        entity, context = RetrieveInstance(entity, context).start()
        # what's returned should be type ServiceInstance
        return entity['entity_res'], context['status'][1]


def all_instance_info():
    """
    Returns information about the service instance.
    Returns all service instances that are accessible to the end-user on this service manager.

    :rtype: List[ServiceInstance]
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        entity = {'entity_id': None, 'entity_req': {}, 'entity_res': None}
        context = {'STORE': STORE, 'RM': RM}
        entity, context = RetrieveAllInstances(entity, context).start()
        return entity['entity_res'], context['status'][1]


def last_operation_status(instance_id, service_id=None, plan_id=None, operation=None):
    """
    Gets the current state of the last operation upon the specified resource.
    When a broker returns status code 202 ACCEPTED for provision, update, or deprovision, the client will
    begin to poll the /v2/service_instances/:guid/last_operation endpoint to obtain the state of the last requested
    operation. The broker response must contain the field state and an optional field description.
    :param instance_id: The instance_id of a service instance is provided by the client. This ID will be used for
    future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.
    :type instance_id: str
    :param service_id: ID of the service from the catalog.
    :type service_id: str
    :param plan_id: ID of the plan from the catalog.
    :type plan_id: str
    :param operation: A broker-provided identifier for the operation. When a value for operation is included
    with asynchronous responses for Provision, Update, and Deprovision requests, the broker client should provide
    the same value using this query parameter as a URL-encoded string.;
    :type operation: str

    :rtype: LastOperation
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        entity = {'entity_id': instance_id,
                  'entity_req': {'service_id':service_id, 'plan_id': plan_id, 'operation': operation},
                  'entity_res': None}
        context = {'STORE': STORE, 'RM': RM}

        entity, context = RetrieveInstanceLastOp(entity, context).start()
        # response should be LastOperation
        return entity['entity_res'], context['status'][1]


def service_bind(instance_id, binding_id, binding):
    """
    Binds to a service
    When the broker receives a bind request from the client, it should return information which helps an application
    to utilize the provisioned resource. This information is generically referred to as credentials. Applications
    should be issued unique credentials whenever possible, so one application access can be revoked without affecting
    other bound applications.
    :param instance_id: The instance_id of a service instance is provided by the client. This ID will be used
    for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.
    :type instance_id: str
    :param binding_id: The binding_id of a service binding is provided by the Cloud Controller.
    :type binding_id: str
    :param binding: 
    :type binding: dict | bytes

    :rtype: BindingResponse
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        # if AAA is enabled and the service is bindable:
        #    create project, user and role bindings
        entity = {'entity_id': instance_id,
                  'entity_req': {'binding_id': binding_id, 'binding': binding},
                  'entity_res': None}
        context = {'STORE': STORE, 'RM': RM, 'AUTH': AUTH}

        entity, context = BindInstance(entity, context).start()
        # response should be a BindingResponse
        return entity['entity_res'], context['status'][1]
        # else:
        #     return 'Not provided as there is no AAA endpoint configured.', 501


def service_unbind(instance_id, binding_id, service_id, plan_id):
    """
    Unbinds a service
    When a broker receives an unbind request from the client, it should delete any resources it created in bind.
    Usually this means that an application immediately cannot access the resource.
    :param instance_id: The instance_id of a service instance is provided by the client. This ID will be used
    for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.
    :type instance_id: str
    :param binding_id: The binding_id of a service binding is provided by the Cloud Controller.
    :type binding_id: str
    :param service_id: ID of the service from the catalog.
    :type service_id: str
    :param plan_id: ID of the plan from the catalog.
    :type plan_id: str

    :rtype: Empty
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        # if AAA is enabled and the service is bindable:
        #    create project, user and role bindings
        entity = {'entity_id': instance_id,
                  'entity_req': {'binding_id': binding_id, 'service_id': service_id, 'plan_id': plan_id},
                  'entity_res': None}
        context = {'STORE': STORE, 'RM': RM, 'AUTH': AUTH}

        entity, context = UnbindInstance(entity, context).start()
        # response should be Empty
        return entity['entity_res'], context['status'][1]
        # else:
        #     return 'Not provided as there is no AAA endpoint configured.', 501


def update_service_instance(instance_id, plan, accept_incomplete=False):
    """
    Updating a Service Instance
    Brokers that implement this endpoint can enable users to modify attributes of an existing service instance.
    The first attribute supports users modifying is the service plan. This effectively enables users to upgrade
    or downgrade their service instance to other plans. To see how users make these requests.&#39;
    :param instance_id: The instance_id of a service instance is provided by the client. This ID will be used
    for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.
    :type instance_id: str
    :param plan: New Plan information.
    :type plan: dict | bytes
    :param accept_incomplete: Indicates that the client is supporting asynchronous operations
    :type accept_incomplete: bool

    :rtype: Empty
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        if connexion.request.is_json:
            plan = UpdateRequest.from_dict(connexion.request.get_json())
        else:
            return "Supplied body content is not or is mal-formed JSON", 400

        entity = {'entity_id': instance_id,
                  'entity_req': {'plan': plan},
                  'entity_res': None}
        context = {'STORE': STORE, 'RM': RM}

        if accept_incomplete:
            AsychExe([UpdateInstance(entity, context)]).start()
            return 'accepted', 201
        else:
            # we have the result of the operation in entity, good/bad status in context
            entity, context = UpdateInstance(entity, context).start()
            # response should be Empty
            return entity['entity_res'], context['status'][1]
