import connexion

from esm.controllers import _version_ok
from esm.models import BindingRequest
from esm.models import BindingResponse
from esm.models import Empty
from esm.models import LastOperation
from esm.models import ServiceInstance
from esm.models import ServiceRequest
from esm.models import ServiceResponse
from esm.models import ServiceType
from esm.models import UpdateOperationResponse
from esm.models import UpdateRequest

from adapters.datasource import STORE as store
from adapters.resources import EPM as epm

# from datetime import date, datetime
# from typing import List, Dict
# from six import iteritems
# from ..util import deserialize_date, deserialize_datetime


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

        # look up manifest based on plan id
        # based on the manifest type, select the driver
        # send the manifest for creation to the target system
        # store the ID along with refs to service, plan and manifest

        # get the manifest for the service/plan
        # TODO some validation required here to ensure it's the right svc/plan
        svc_type = store.get_service(service.service_id)[0]
        if svc_type is None:
            return 'Unrecognised service requested to be instantiated', 404

        plans = svc_type.plans
        plan = [p for p in plans if p.id == service.plan_id]
        if len(plan) <= 0:
            return 'no plan found.', 404

        mani = store.get_manifest(plan_id=plan[0].id)[0]

        if accept_incomplete:  # given docker-compose runs in detached mode this is not needed - only timing can verify
            # XXX put this in a thread to allow for asynch processing?
            epm.create(instance_id=instance_id, content=mani.manifest_content, c_type=mani.manifest_type)
        else:
            epm.create(instance_id=instance_id, content=mani.manifest_content, c_type=mani.manifest_type)

        last_op = LastOperation(
            state='creating',
            description='service instance is being created'
        )

        # store.add_last_operation(instance_id, last_op)

        # store the instance Id with manifest id
        srv_inst = ServiceInstance(
            service_type=svc_type,
            state=last_op,
            context={
                'id': instance_id,
                'manifest_id': mani.id,
            }
        )

        store.add_service_instance(srv_inst)

        if accept_incomplete:
            store.add_last_operation(instance_id=instance_id, last_operation=last_op)

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
        epm.delete(instance_id=instance_id)
        store.delete_service_instance(instance_id)
        # we don't delete the last_operation explicitly as its embedded in the service_instance document
        # store.delete_last_operation(instance_id)

        return Empty(), 200


def instance_info(instance_id):
    """
    Returns information about the service instance.
    Returns information about the service instance. This is a simple read operation against the broker database and
    is provided as a developer/consumer convienence.
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used
    for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39;
    :type instance_id: str

    :rtype: ServiceType
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        # service instance should already be recorded
        srv_inst = store.get_service_instance(instance_id)
        if len(srv_inst) < 1:
            return 'no service instance found.', 404
        srv_inst = srv_inst[0]

        # get the latest info
        inst_info = epm.info(instance_id=instance_id)

        if inst_info['srv_inst.state.state'] == 'failed':
            # try epm.delete(instance_id=instance_id)?
            return 'There has been a failure in creating the service instance.', 500

        # TODO need a converged state model for the SM
        srv_inst.state.state = inst_info['srv_inst.state.state']
        srv_inst.state.description = inst_info['srv_inst.state.description']

        # don't need you any more, buh-bye!
        del inst_info['srv_inst.state.state']
        del inst_info['srv_inst.state.description']

        # merge the two context dicts
        srv_inst.context = {**srv_inst.context, **inst_info}

        # update the service instance record - there should be an asynch method doing the update - event based
        store.add_service_instance(srv_inst)

        return srv_inst, 200


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
    # just re-use the method and return it's content and http status code.
    # version check not required here as it's done in the proxied call
    srv_inst, code = instance_info(instance_id=instance_id)
    return srv_inst.state, code


def service_bind(instance_id, binding_id, binding):
    """
    Binds to a service
    When the broker receives a bind request from the client, it should return information which helps an application to utilize the provisioned resource. This information is generically referred to as credentials. Applications should be issued unique credentials whenever possible, so one application access can be revoked without affecting other bound applications. 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
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
        return 'Not implemented :-(', 501


def service_unbind(instance_id, binding_id, service_id, plan_id):
    """
    Unbinds a service
    When a broker receives an unbind request from the client, it should delete any resources it created in bind. Usually this means that an application immediately cannot access the resource. 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
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
        return 'Not implemented :-(', 501


def update_service_instance(instance_id, plan, accept_incomplete=None):
    """
    Updating a Service Instance
    Brokers that implement this endpoint can enable users to modify attributes of an existing service instance. The first attribute supports users modifying is the service plan. This effectively enables users to upgrade or downgrade their service instance to other plans. To see how users make these requests.&#39; 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
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
