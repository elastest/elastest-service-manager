import connexion
from pymongo import MongoClient

# from adapters.epm import DockerBackend as EPM
# from adapters.docker import DummyBackend as EPM
from adapters.epm import EPM

from esm.models import BindingRequest
from esm.models import BindingResponse
from esm.models import Empty
# from esm.models.error import Error
from esm.models import LastOperation
from esm.models import Manifest
from esm.models import ServiceInstance
from esm.models import ServiceRequest
from esm.models import ServiceResponse
from esm.models import ServiceType
from esm.models import UpdateOperationResponse
from esm.models import UpdateRequest

from adapters.datasource import ESM_DB

from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


epm = EPM()


def create_service_instance(instance_id, service, accept_incomplete=None):
    """
    Provisions a service instance
    When the broker receives a provision request from a client, it should synchronously take whatever action is necessary to create a new service resource for the developer. The result of provisioning varies by service type, although there are a few common actions that work for many services. Supports asynchronous operations.&#39; 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str
    :param service: Service information.
    :type service: dict | bytes
    :param accept_incomplete: Indicates that the client is supporting asynchronous operations
    :type accept_incomplete: bool

    :rtype: ServiceResponse
    """
    if connexion.request.is_json:
        service = ServiceRequest.from_dict(connexion.request.get_json())

    # look up manifest based on plan id
    # based on the manifest type, select the driver
    # send the manifest for creation to the target system
    # store the ID along with refs to service, plan and manifest

    # get the manifest for the service/plan
    # TODO some validation required here to ensure it's the right svc/plan
    # we will use this later... so will not use .count
    svc_type_raw = ESM_DB.services.find_one({'id': service.service_id})
    if svc_type_raw is None:
        return 'Unrecognised service requested to be instantiated', 404

    plans = ESM_DB.services.find_one({'id': service.service_id})['plans']
    plan = [p for p in plans if p['id'] == service.plan_id]
    if len(plan) <= 0:
        return 'no plan found.', 404

    mani_raw = ESM_DB.manifests.find_one({'plan_id': service.plan_id})
    if mani_raw is None:
        return 'Unrecognised manifest requested to be instantiated', 404
    mani = Manifest.from_dict(mani_raw)

    if accept_incomplete:  # given docker-compose runs in detached mode this is not needed - only timing can verify
        # TODO put this in a thread to allow for asynch processing
        epm.create(instance_id=instance_id, content=mani.manifest_content, type=mani.manifest_type)
    else:
        epm.create(instance_id=instance_id, content=mani.manifest_content, type=mani.manifest_type)

    last_op = LastOperation(
        state='creating',
        description='service instance is being created'
    )

    # store the instance Id with manifest id
    srv_inst = ServiceInstance(
        service_type=ServiceType.from_dict(svc_type_raw),
        state=last_op,
        context={
            'id': instance_id,
            'manifest_id': mani.id,
        }
    )
    result = ESM_DB.instances.insert_one(srv_inst.to_dict())
    if not result.acknowledged:
        return 'there was an issue saving the service instance to the DB', 500

    if accept_incomplete:
        result = ESM_DB.last_operations.insert_one({'id': instance_id, 'last_op': last_op.to_dict()})
        if not result.acknowledged:
            return 'there was an issue saving the service status to the DB', 500

    return 'created', 200


def deprovision_service_instance(instance_id, service_id, plan_id, accept_incomplete=None):
    """
    Deprovisions a service instance.
    &#39;When a broker receives a deprovision request from a client, it should delete any resources it created during the provision. Usually this means that all resources are immediately reclaimed for future provisions.&#39; 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str
    :param service_id: service ID to be deprovisioned
    :type service_id: str
    :param plan_id: plan ID of the service to be deprovisioned
    :type plan_id: str
    :param accept_incomplete: Indicates that the client is supporting asynchronous operations
    :type accept_incomplete: bool

    :rtype: UpdateOperationResponse
    """
    # XXX if there's bindings remove first?
    epm.delete(instance_id=instance_id)

    return Empty(), 200


def instance_info(instance_id):
    """
    Returns information about the service instance.
    Returns information about the service instance. This is a simple read operation against the broker database and is provided as a developer/consumer convienence. 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str

    :rtype: ServiceType
    """

    # service instance should already be recorded
    srv_inst = ESM_DB.instances.find_one({'context.id': instance_id})

    if srv_inst is None:
        return 'no service instance found.', 404

    record_id = srv_inst['_id']
    srv_inst = ServiceInstance.from_dict(srv_inst)
    # get the latest info
    inst_info = epm.info(instance_id=instance_id)

    # merge the status dicts  # TODO move this functionality into the adapter
    states = set([v for k, v in inst_info.items() if k.endswith('state')])

    # states from compose.container.Container: 'Paused', 'Restarting', 'Ghost', 'Up', 'Exit %s'
    # states for OSBA: in progress, succeeded, and failed
    for state in states:
        if state.startswith('Exit'):
            # there's been an error with docker
            srv_inst.state.state = 'failed'
            srv_inst.state.description = 'There was an error in creating the instance {error}'.format(error=state)
            return 'Error with docker: {error}'.format(error=state), 500

    if len(states) == 1:  # if all states of the same value
        if states.pop() == 'Up':  # if running: Up
            print('containers complete')
            srv_inst.state.state = 'succeeded'
            srv_inst.state.description = 'The service instance has been created successfully'
    else:
        # still waiting for completion
        print('Waiting for completion')
        srv_inst.state.state = 'in progress'
        srv_inst.state.description = 'The service instance is being created.'

    # merge the two context dicts
    srv_inst.context = {**srv_inst.context, **inst_info}
    # update the service instance record - there should be an asynch method doing the update - event based
    result = ESM_DB.instances.update_one({'_id': record_id}, {"$set": srv_inst.to_dict()}, upsert=False)

    if not result.acknowledged:
        return 'there was an issue updating the service instance to the DB', 500

    return srv_inst.to_dict(), 200


def last_operation_status(instance_id, service_id=None, plan_id=None, operation=None):
    """
    Gets the current state of the last operation upon the specified resource.
    \&quot;When a broker returns status code 202 ACCEPTED for provision, update, or deprovision, the client will begin to poll the /v2/service_instances/:guid/last_operation endpoint to obtain the state of the last requested operation. The broker response must contain the field state and an optional field description.\&quot; 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str
    :param service_id: ID of the service from the catalog.
    :type service_id: str
    :param plan_id: ID of the plan from the catalog.
    :type plan_id: str
    :param operation: \&quot;A broker-provided identifier for the operation. When a value for operation is included with asynchronous responses for Provision, Update, and Deprovision requests, the broker client should provide the same value using this query parameter as a URL-encoded string.\&quot; 
    :type operation: str

    :rtype: LastOperation
    """

    # just re-use the method and return it's http status code.
    inst_info = instance_info(instance_id=instance_id)
    si = ServiceInstance.from_dict(inst_info[0])
    return si.state.to_dict(), inst_info[1]


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
    if connexion.request.is_json:
        binding = BindingRequest.from_dict(connexion.request.get_json())
    return 'do some magic!'


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
    return 'do some magic!'


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
    if connexion.request.is_json:
        plan = UpdateRequest.from_dict(connexion.request.get_json())
    return 'do some magic!'
