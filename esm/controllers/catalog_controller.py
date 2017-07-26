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
from esm.controllers import _version_ok
from esm.models.catalog import Catalog
from esm.models.empty import Empty
from esm.models.service_type import ServiceType
from esm.models.manifest import Manifest
# from datetime import date, datetime
# from typing import List, Dict
# from six import iteritems
# from ..util import deserialize_date, deserialize_datetime

from adapters.datasource import STORE


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
        manifest.id = manifest_id

        result, code = STORE.add_manifest(manifest)

        if code == 200:
            return Empty(), code
        else:
            return result, code
