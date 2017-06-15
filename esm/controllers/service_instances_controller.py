import connexion
from esm.models.binding import Binding
from esm.models.binding_response import BindingResponse
from esm.models.dashboard_url import DashboardUrl
from esm.models.empty import Empty
from esm.models.error import Error
from esm.models.service import Service
from esm.models.service_plan import ServicePlan
from esm.models.update_operation import UpdateOperation
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def create_service_instance(instance_id, service, accept_incomplete=None):
    """
    Provisions a service instance
    &#39;When the broker receives a provision request from a client, it should synchronously take whatever action is necessary to create a new service resource for the developer. The result of provisioning varies by service type, although there are a few common actions that work for many services. Supports asynchronous operations.&#39; 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str
    :param service: Service information.
    :type service: dict | bytes
    :param accept_incomplete: Indicates that the client is supporting asynchronous operations
    :type accept_incomplete: str

    :rtype: DashboardUrl
    """
    if connexion.request.is_json:
        service = Service.from_dict(connexion.request.get_json())
    return 'do some magic!'


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
    :type accept_incomplete: str

    :rtype: Empty
    """
    return 'do some magic!'


def service_bind(instance_id, binding_id, binding):
    """
    Binds to a service
    &#39;When the broker receives a bind request from the client, it should return information which helps an application to utilize the provisioned resource. This information is generically referred to as credentials. Applications should be issued unique credentials whenever possible, so one application access can be revoked without affecting other bound applications.&#39; 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str
    :param binding_id: The binding_id of a service binding is provided by the Cloud Controller.
    :type binding_id: str
    :param binding: 
    :type binding: dict | bytes

    :rtype: BindingResponse
    """
    if connexion.request.is_json:
        binding = Binding.from_dict(connexion.request.get_json())
    return 'do some magic!'


def service_unbind(instance_id, binding_id, service_id, plan_id):
    """
    Unbinds a service
    &#39;When a broker receives an unbind request from the client, it should delete any resources it created in bind. Usually this means that an application immediately cannot access the resource.&#39; 
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
    &#39;Brokers that implement this endpoint can enable users to modify attributes of an existing service instance. The first attribute supports users modifying is the service plan. This effectively enables users to upgrade or downgrade their service instance to other plans. To see how users make these requests.&#39; 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str
    :param plan: New Plan information.
    :type plan: dict | bytes
    :param accept_incomplete: Indicates that the client is supporting asynchronous operations
    :type accept_incomplete: str

    :rtype: Empty
    """
    if connexion.request.is_json:
        plan = ServicePlan.from_dict(connexion.request.get_json())
    return 'do some magic!'
