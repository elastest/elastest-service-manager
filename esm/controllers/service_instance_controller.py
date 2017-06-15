import connexion
from esm.models.catalog_service import CatalogService
from esm.models.last_operation import LastOperation
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def instance_info(instance_id):
    """
    Returns information about the service instance.
    Returns information about the service instance. This is a simple read operation against the broker database  and is provided as a developer/consumer convienence. 
    :param instance_id: &#39;The instance_id of a service instance is provided by the client. This ID will be used for future requests (bind and deprovision), so the broker must use it to correlate the resource it creates.&#39; 
    :type instance_id: str

    :rtype: CatalogService
    """
    return 'do some magic!'


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
    return 'do some magic!'
