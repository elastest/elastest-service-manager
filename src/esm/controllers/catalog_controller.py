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
from flask import request, Response
from functools import wraps

from adapters.store import STORE
from esm.controllers import _version_ok

from esm.models.catalog import Catalog
from esm.models.empty import Empty
from esm.models.manifest import Manifest
from esm.models.service_type import ServiceType

# from datetime import date, datetime
# from typing import List, Dict
# from six import iteritems
# from ..util import deserialize_date, deserialize_datetime


# def check_auth(username, password):
#     """This function is called to check if a username /
#     password combination is valid.
#     """
#     return username == 'admin' and password == 'secret'
#
#
# def authenticate():
#     """Sends a 401 response that enables basic auth"""
#     return Response(
#     'Could not verify your access level for that URL.\n'
#     'You have to login with proper credentials', 401,
#     {'WWW-Authenticate': 'Basic realm="Login Required"'})
#
#
# def requires_auth(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         auth = request.authorization
#         if not auth or not check_auth(auth.username, auth.password):
#             return authenticate()
#         return f(*args, **kwargs)
#     return decorated


# @requires_auth
def catalog():
    """
    Gets services registered within the broker
    \&quot;The first endpoint that a broker must implement is the service catalog. The client will initially fetch
    this endpoint from all brokers and make adjustments to the user-facing service catalog stored in the a
    client database. \\n\&quot;

    :rtype: Catalog
    """
    # get all services from the service collection

    ok, message, code = _version_ok()

    if not ok:
        return message, code
    else:
        services = STORE.get_service()
        return Catalog(services=services), 200


def register_service(service):
    """
    Registers the service with the catalog.
    \&quot;Service providers need a means to register their service with a service broker. This provides this
    functionality. Also using PUT a service provider can update their registration. Note that this requires the
    complete content and will REPLACE the existing service information registered with the broker.\&quot;
    :param service: the service description to register
    :type service: dict | bytes

    :rtype: Empty
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        if connexion.request.is_json:
            service = ServiceType.from_dict(connexion.request.get_json())
        else:
            return "Supplied body content is not or is mal-formed JSON", 400
        STORE.add_service(service=service)
        return Empty()


def delete_service_type(service_id):  # noqa: E501
    """Deletes a registered service type

    Deletes a service that is already registered with the service manager.
    It does not delete the manifest or plan associated with the service type.  # noqa: E501

    :param service_id: service ID to be deleted
    :type service_id: str

    :rtype: Empty
    """
    srv = STORE.get_service(service_id)
    # expectation: if not found, srv is None
    if srv:
        STORE.delete_service(service_id)
        return Empty()
    else:
        return "Service type not found", 404


def store_manifest(manifest_id, manifest):
    """
    takes deployment description of a software service and associates with a service and plan
    takes deployment description of a software service and associates with a service and plan that is already
    registered in the service catalog.
    :param manifest_id: The manifest_id of a manifest to be associated with a plan of a servicetype.
    :type manifest_id: str
    :param manifest: the manifest to store
    :type manifest: dict | bytes

    :rtype: ServiceResponse
    """
    ok, message, code = _version_ok()
    if not ok:
        return message, code
    else:
        if connexion.request.is_json:
            manifest = Manifest.from_dict(connexion.request.get_json())
        else:
            return "Supplied body content is not or is mal-formed JSON", 400
        if manifest.manifest_content.find('</br>') > 0:  # TODO(dizz) remove this check in R4
            return "Manifest content contains '</br>'. Please remove these and replace with '\n'", 400
        manifest.id = manifest_id

        result, code = STORE.add_manifest(manifest)

        if code == 200:
            return Empty(), code
        else:
            return result, code


def get_manifest(manifest_id):
    """
    returns a specific of manifest registered at with the ESM
    hi!
    :param manifest_id: The manifest_id of a manifest to be associated with a plan of a servicetype.
    :type manifest_id: str

    :rtype: Manifest
    """

    manifest = STORE.get_manifest(manifest_id)

    if len(manifest) > 0:
        return manifest, 200
    else:
        return 'Manifest {id} could not be found'.format(id=manifest_id), 404


def list_manifests():
    """
    returns a list of manifests registered at with the ESM
    hi!

    :rtype: List[Manifest]
    """
    manifests = STORE.get_manifest()
    return manifests, 200
