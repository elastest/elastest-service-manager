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
import flask
import os
import signal

from healthcheck import HealthCheck, EnvironmentDump
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.wsgi import WSGIContainer

import config
from adapters.log import get_logger
from adapters.store import STORE
from adapters.resources import RM
from esm.encoder import JSONEncoder


LOG = get_logger(__name__)


# this adds keystone auth to access the ESM
def add_mware(app):
    # See: https://docs.openstack.org/keystonemiddleware/latest/middlewarearchitecture.html
    if config.auth_base_url != '':
        from keystonemiddleware import auth_token

        base_url = config.auth_base_url
        admin_port = config.auth_admin_port
        user_port = config.auth_user_port
        username = config.auth_username
        passwd = config.auth_passwd
        tenant = config.auth_tenant

        if '' in [username, passwd, tenant]:
            raise RuntimeError('Keystone admin username, password or tenant name is not set in the environment.')

        conf = {
            'service_token_roles_required': True,
            'identity_uri': base_url + ':' + str(admin_port) + '/',
            'auth_version': 'v3.0',
            'www_authenticate_uri': base_url + ':' + str(user_port) + '/v3/',
            'admin_user': username,
            'admin_password': passwd,
            'admin_tenant_name': tenant,
        }
        return auth_token.AuthProtocol(app, conf)
    else:
        return app


def add_check_api():
    app = flask.Flask('check_api')
    health = HealthCheck(app, "/health")
    envdump = EnvironmentDump(app, "/environment")

    def health_check():
        db_engines_ok = STORE.is_ok()  # calls specific DB check
        resource_engine_ok = RM.is_ok()  # calls specific RM check
        this_ok = (1 + 1 == 2)  # basic local check
        # maintenance = False

        if this_ok and db_engines_ok and resource_engine_ok:
            return {'status', 'up'}
        # elif not maintenance:
        #     return {'status', 'out_of_service'}
        else:
            return {'status', 'down'}

    def application_data():
        return {'maintainer': 'ElasTest',
                'git_repo': 'https://github.com/elastest/elastest-service-manager'}

    health.add_check(health_check)
    envdump.add_section("application", application_data)

    return add_mware(app)


def create_api():
    filename = os.path.join(os.path.dirname(__file__), 'esm/swagger/')
    app = connexion.App('esm_api', specification_dir=filename)
    app.app.json_encoder = JSONEncoder
    app.add_api(
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
    LOG.info('OSBA API and ElasTest extensions API created.')
    return add_mware(app)


def shutdown_handler(signum=None, frame=None):
    LOG.info('Shutting down...')
    IOLoop.instance().stop()


if __name__ == '__main__':
    esm_ip = config.esm_bind_address
    esm_port = config.esm_bind_port
    esm_server = HTTPServer(WSGIContainer(create_api()))
    esm_server.listen(address=esm_ip, port=esm_port)
    LOG.info('ESM available at http://{IP}:{PORT}'.format(IP=esm_ip, PORT=esm_port))

    esm_check_ip = config.esm_check_ip
    check_port = config.esm_check_port
    check_server = HTTPServer(WSGIContainer(add_check_api()))
    check_server.listen(address=esm_check_ip, port=check_port)
    LOG.info('ESM Health available at http://{IP}:{PORT}'.format(IP=esm_check_ip, PORT=check_port))

    for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
        signal.signal(sig, shutdown_handler)

    LOG.info(config.print_env_vars())
    LOG.info('Press CTRL+C to quit.')
    IOLoop.instance().start()
