#!/usr/bin/env python3
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

import os

import connexion
from esm.encoder import JSONEncoder

from adapters.log import LOG


if __name__ == '__main__':
    ESM_APP = connexion.App(__name__, specification_dir='./esm/swagger/')
    ESM_APP.app.json_encoder = JSONEncoder
    # TODO consider overriding Resolver if OO holders of controller methods is required.
    ESM_APP.add_api(
        'swagger.yaml', strict_validation=True,
        arguments={'title': 'The Open Service Broker API defines the contract between the a requesting '
                            'client and the service broker. The broker is expected to implement several '
                            'HTTP (or HTTPS) endpoints underneath a URI prefix. One or more services can '
                            'be provided by a single broker, and load balancing enables horizontal '
                            'scalability of redundant brokers. Multiple service provider instances can be '
                            'supported by a single broker using different URL prefixes and credentials. '
                            '[Learn more about the Service Broker API.] '
                            '(https://github.com/openservicebrokerapi/servicebroker/). Note the '
                            '[topic on orphan resolution]'
                            '(https://github.com/openservicebrokerapi/servicebroker/blob/master/_spec.md#orphans). '
                            'It is not dealt with in this spec. '
                   }
    )

    ESM_APP.app.logger.setLevel('DEBUG')
    ESM_PORT = os.environ.get('ESM_PORT', 8080)
    ESM_APP.app.logger.info(' * ESM_PORT: ' + str(ESM_PORT))
    LOG.info(' * ESM_PORT: ' + str(ESM_PORT))
    ESM_APP.run(host='0.0.0.0', port=ESM_PORT)
