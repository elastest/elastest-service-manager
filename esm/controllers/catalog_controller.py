import connexion
from esm.models.catalog import Catalog
from esm.models.empty import Empty
from esm.models.error import Error
from esm.models.manifest import Manifest
from esm.models.service_type import ServiceType
from esm.models.manifest import Manifest
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime

# TODO externalise this
from pymongo import MongoClient
CLIENT = MongoClient('localhost', 27017)  # take from env
ESM_DB = CLIENT.esm


def catalog():
    """
    Gets services registered within the broker
    \&quot;The first endpoint that a broker must implement is the service catalog. The client will initially fetch this endpoint from all brokers and make adjustments to the user-facing service catalog stored in the a client database. \\n\&quot;

    :rtype: Catalog
    """
    # get all services from the service collection

    # page_number = connexion.request.headers['Page-Number']

    service_catalog = Catalog(services=[])

    for service in ESM_DB.services.find():
        service_catalog.services.append(ServiceType(service.id).from_dict(service))

    # note that if we had many services this could be expensive in terms of memory usage
    return service_catalog


def register_service(service):
    """
    Registers the service with the catalog.
    \&quot;Service providers need a means to register their service with a service broker. This provides this functionality. Also using PUT a service provider can update their registration. Note that this requires the complete content and will REPLACE the existing service information registered with the broker.\&quot;
    :param service: the service description to register
    :type service: dict | bytes

    :rtype: Empty
    """
    if connexion.request.is_json:
        service = ServiceType.from_dict(connexion.request.get_json())

    # save to DB
    services = ESM_DB.services

    if services.count({'id': service.id}) == 0:
        result = services.insert_one(service.to_dict())
        if not result.acknowledged:
            return 'there was an issue saving the supplied service type to the DB', 500
    else:
        return 'the service already exists in the catalog. you should resubmit with a different service.', 409

    return Empty()


def store_manifest(manifest_id, manifest):
    """
    takes deployment description of a software service and associates with a service and plan
    takes deployment description of a software service and associates with a service and plan that is already registered in the service catalog.
    :param manifest_id: The manifest_id of a manifest to be associated with a plan of a servicetype.
    :type manifest_id: str
    :param manifest: the manifest to store
    :type manifest: dict | bytes

    :rtype: ServiceResponse
    """

    if connexion.request.is_json:
        manifest = Manifest.from_dict(connexion.request.get_json())

    services = ESM_DB.services

    # ensure the manifest-defined service and plan id exist
    if services.count({'id': manifest.service_id}) > 0:
        # get the plans
        plans = services.find_one({'id': manifest.service_id})['plans']
        # filter the plans to find the plan to be associated with
        plan = [p for p in plans if p['id'] == manifest.plan_id]
        if len(plan) != 1:
            return 'no plan or duplicate plan found.', 401
    else:
        return 'the service id in the supplied manifest does not exist.', 404

    # save to DB
    manifests = ESM_DB.manifests

    manifest.id = manifest_id
    if manifests.count({'id': manifest.id}) == 0:
        result = manifests.insert_one(manifest.to_dict())
        if not result.acknowledged:
            return 'there was an issue saving the supplied manifest to the DB', 500
    else:
        print('client side error - 4XX')
        return 'the manifest already exists in the catalog', 409

    return Empty()
