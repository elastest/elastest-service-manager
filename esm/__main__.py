#!/usr/bin/env python3

import connexion
from .encoder import JSONEncoder


if __name__ == '__main__':
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.app.json_encoder = JSONEncoder
    app.add_api('swagger.yaml', arguments={'title': 'This is the service manager API. It is an extension of the the Open Service Broker API (v2.12). The Open Service Broker API defines the contract between the a requesting client and the service broker. The broker is expected to implement several HTTP (or HTTPS) endpoints underneath a URI prefix. One or more services can be provided by a single broker, and load balancing enables horizontal scalability of redundant brokers. Multiple service provider instances can be supported by a single broker using different URL prefixes and credentials. [Learn more about the Service Broker API.] (https://github.com/openservicebrokerapi/servicebroker/). Note the [topic on orphan resolution](https://github.com/openservicebrokerapi/servicebroker/blob/master/_spec.md#orphans). It is not dealt with in this spec. '})
    app.run(port=8080)
