import connexion
from esm.models.catalog_service import CatalogService
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
