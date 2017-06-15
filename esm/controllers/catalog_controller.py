import connexion
from esm.models.catalog_service import CatalogService
from esm.models.catalog_services import CatalogServices
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def catalog():
    """
    Gets services registered within the broker
    \&quot;The first endpoint that a broker must implement is the service catalog. The client will initially fetch this endpoint from all brokers and make adjustments to the user-facing service catalog stored in the a client database. \\n\&quot; 

    :rtype: CatalogServices
    """
    return 'do some magic!'


def register_service(service):
    """
    Registers the service with the catalog.
    \&quot;Service providers need a means to register their service with a service broker. This provides this functionality. Also using PUT a service provider can update their registration. Note that this requires the complete content and will REPLACE the existing service information registered with the broker.\&quot; 
    :param service: the service description to register
    :type service: dict | bytes

    :rtype: CatalogServices
    """
    if connexion.request.is_json:
        service = CatalogService.from_dict(connexion.request.get_json())
    return 'do some magic!'
