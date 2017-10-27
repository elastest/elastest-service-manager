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

from adapters.datasource import STORE
from adapters.resources import RM
from esm.controllers import _version_ok

from esm.models.binding_request import BindingRequest
from esm.models.binding_response import BindingResponse
from esm.models.empty import Empty
from esm.models.last_operation import LastOperation
from esm.models.service_instance import ServiceInstance
from esm.models.service_request import ServiceRequest
from esm.models.service_response import ServiceResponse
from esm.models.service_type import ServiceType
from esm.models.update_operation_response import UpdateOperationResponse
from esm.models.update_request import UpdateRequest


# TODO need a converged state model for the SM - see info methods of backend


def create_service_instance(instance_id, service, accept_incomplete=None):
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
            service = ServiceRequest.from_dict(connexion.request.get_json())
        else:
            return "Supplied body content is not or is mal-formed JSON", 400

        svc_type = STORE.get_service_instance(service.service_id)
        if len(svc_type) == 1:
            return 'Service instance with id {id} already exists'.format(id=service.service_id), 409
        # look up manifest based on plan id
        # based on the manifest type, select the driver
        # send the manifest for creation to the target system
        # store the ID along with refs to service, plan and manifest

        # get the manifest for the service/plan
        # TODO some validation required here to ensure it's the right svc/plan
        svc_type = STORE.get_service(service.service_id)[0]
        if svc_type is None:
            return 'Unrecognised service requested to be instantiated', 404

        plans = svc_type.plans
        plan = [p for p in plans if p.id == service.plan_id]
        if len(plan) <= 0:
            return 'no plan found.', 404

        mani = STORE.get_manifest(plan_id=plan[0].id)
        if len(mani) <= 0:
            return 'no manifest for service {plan} found.'.format(plan=service.plan_id), 404
        mani = mani[0]

        if accept_incomplete:  # given docker-compose runs in detached mode this is not needed - only timing can verify
            # XXX put this in a thread to allow for asynch processing?
            RM.create(instance_id=instance_id, content=mani.manifest_content,
                      c_type=mani.manifest_type, parameters=service.parameters)
        else:
            RM.create(instance_id=instance_id, content=mani.manifest_content,
                      c_type=mani.manifest_type, parameters=service.parameters)

        last_op = LastOperation(  # stored within the service instance doc
            state='creating',
            description='service instance is being created'
        )

        # store the instance Id with manifest id
        srv_inst = ServiceInstance(
            service_type=svc_type,
            state=last_op,
            context={
                'id': instance_id,
                'manifest_id': mani.id,
            }
        )

        STORE.add_service_instance(srv_inst)

        if accept_incomplete:
            STORE.add_last_operation(instance_id=instance_id, last_operation=last_op)

        return 'created', 200


def deprovision_service_instance(instance_id, service_id, plan_id, accept_incomplete=None):
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
        # XXX if there's bindings remove first?
        # XXX what about undo?
        # check that the instance exists first
        instance = STORE.get_service_instance(instance_id=instance_id)
        if len(instance) == 1:
            mani_id = instance[0].context['manifest_id']
            mani = STORE.get_manifest(manifest_id=mani_id)
            if len(mani) < 1:
                return 'no service manifest found.', 404

            RM.delete(instance_id=instance_id, manifest_type=mani[0].manifest_type)
            STORE.delete_service_instance(instance_id)
            # we don't delete the last_operation explicitly as its embedded in the service_instance document
            # STORE.delete_last_operation(instance_id)

            return Empty(), 200
        else:
            return Empty(), 404


def _get_instance(srv_inst):
    # get the latest info
    mani_id = srv_inst.context['manifest_id']
    mani = STORE.get_manifest(manifest_id=mani_id)
    if len(mani) < 1:
        return 'no manifest found.', 404
    # Get the latest info of the instance
    # could also use STORE.get_service_instance(srv_inst) but will not have all details
    inst_info = RM.info(instance_id=srv_inst.context['id'], manifest_type=mani[0].manifest_type)

    if inst_info['srv_inst.state.state'] == 'failed':
        # try epm.delete(instance_id=instance_id)?
        return 'There has been a failure in creating the service instance.', 500

    srv_inst.state.state = inst_info['srv_inst.state.state']
    srv_inst.state.description = inst_info['srv_inst.state.description']

    # don't need you any more, buh-bye!
    del inst_info['srv_inst.state.state']
    del inst_info['srv_inst.state.description']

    # merge the two context dicts
    srv_inst.context = {**srv_inst.context, **inst_info}

    # update the service instance record - there should be an asynch method doing the update - event based
    STORE.add_service_instance(srv_inst)

    return srv_inst


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
        # service instance should already be recorded
        srv_inst = STORE.get_service_instance(instance_id)
        if len(srv_inst) < 1:
            return 'no service instance found.', 404
        srv_inst = srv_inst[0]

        srv_inst = _get_instance(srv_inst)

        return srv_inst, 200


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
        instances = STORE.get_service_instance()
        insts = list()
        for inst in instances:
            insts.append(_get_instance(inst))

        return insts, 200


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
        # just re-use the method and return it's content and http status code.
        # version check not required here as it's done in the proxied call
        srv_inst, code = instance_info(instance_id=instance_id)
        if code == 404:
            return srv_inst + 'No service status therefore.', code
        else:
            return srv_inst.state, code


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
        if connexion.request.is_json:
            binding = BindingRequest.from_dict(connexion.request.get_json())
        else:
            return "Supplied body content is not or is mal-formed JSON", 400
        return 'Not implemented. Pending selection and integration of an ET identity service', 501


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
        return 'Not implemented. Pending selection and integration of an ET identity service', 501


def update_service_instance(instance_id, plan, accept_incomplete=None):
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
        return 'Not implemented :-(', 501
