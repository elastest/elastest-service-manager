"""This starts the ESM"""


import os

import connexion
from esm.encoder import JSONEncoder


if __name__ == '__main__':
    ESM_APP = connexion.App(__name__, specification_dir='./esm/swagger/')
    ESM_APP.app.json_encoder = JSONEncoder
    ESM_APP.add_api('swagger.yaml', arguments={'title': 'The Open Service Broker API defines the contract between the a requesting client and the service broker. The broker is expected to implement several HTTP (or HTTPS) endpoints underneath a URI prefix. One or more services can be provided by a single broker, and load balancing enables horizontal scalability of redundant brokers. Multiple service provider instances can be supported by a single broker using different URL prefixes and credentials. [Learn more about the Service Broker API.] (https://github.com/openservicebrokerapi/servicebroker/). Note the [topic on orphan resolution](https://github.com/openservicebrokerapi/servicebroker/blob/master/_spec.md#orphans). It is not dealt with in this spec. '})
    ESM_PORT = os.environ.get('ESM_PORT', 8080)
    print(' * SB_PORT: ' + str(ESM_PORT))
    ESM_APP.run(port=ESM_PORT)
