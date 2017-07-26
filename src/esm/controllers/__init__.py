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


def _version_ok():
    # TODO create a decorator out of this

    version_requested = connexion.request.headers.get('X-Broker-Api-Version', None)

    if not version_requested:
        return False, 'No X-Broker-Api-Version header supplied in the request. This endpoint supports 2.12.', 400
    elif version_requested != '2.12':
        return False, 'The X-Broker-Api-Version header is not supported. This endpoint supports 2.12.', 400
    else:
        return True, 'Requested API version is acceptable.', 201
