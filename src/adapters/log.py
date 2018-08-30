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

import jsonpickle
import logging
from time import sleep

import docker
import json
from kafka import KafkaProducer
import requests

import config


def get_logger(name, level=logging.DEBUG, space=None, series=None, sentinel=False):  # pragma: sentinel NO cover
    if config.sen_kafka_ep != '' and sentinel:
        logger = logging.getLogger(name)
        logger.setLevel(level)

        logger.info('Adding Sentinel logging handler')
        handler = SentinelLogHandler(backup_file='backup.log', space=space, series=series)
        handler.setLevel(level)
        logger.addHandler(handler)

        print('reading...', config.sen_topic)
    else:
        logging.basicConfig(level=level)
        logger = logging.getLogger(name)

    logger.setLevel(level)
    return logger


class SentinelLogHandler(logging.Handler):  # pragma: sentinel NO cover
    """Kafka logger handler attempts to write python logs directly
    into specified kafka topic instead of writing them into file.
    """

    def setLevel(self, level):
        super().setLevel(level)

    def __init__(self, backup_file=None, space=None, series=None):
        logging.Handler.__init__(self)
        self.space = space
        self.series = series
        # Backup log file for errors
        self.fail_fh = backup_file
        if self.fail_fh is not None:
            self.fail_fh = open(backup_file, 'w')

    @staticmethod
    def format_msg(record):
        msg_dict = {}
        msg_dict['level'] = 'WARN'  # logging.getLevelName(self.level)
        msg_dict['msg'] = record

        return msg_dict

    def emit(self, record):
        # drop kafka logging to avoid infinite recursion
        if record.name == 'kafka':
            return
        try:
            print('emitting...', record.msg)
            msg_dict = {'msg': record.msg}
            if '#' in record.msg:
                msg_dict['instance_id'], msg_dict['msg'] = record.msg.split('#')
            msg_dict['level'] = logging.getLevelName(self.level)
            msg_dict['file'] = __file__

            # msg = self.format_msg(record)
            print('Preparing to send log-payload: ', msg_dict)
            self._send_msg(msg_dict)

        except AttributeError:
            self.write_backup("Kafka Error!")
            self.write_backup(record)
            pass
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            # Log errors due queue full
            self.write_backup(record)
            self.handleError(record)

    def write_backup(self, record):
        if self.fail_fh:
            self.fail_fh.write(str(record) + "\n")

    def close(self):
        if self.fail_fh:
            self.fail_fh.close()
        logging.Handler.close(self)

    def _get_kafka_producer(self, endpoint, key_serializer, value_serializer):
        if key_serializer == "StringSerializer" and value_serializer == "StringSerializer":
            return KafkaProducer(linger_ms=1, acks='all', retries=0, key_serializer=str.encode,
                                 value_serializer=str.encode, bootstrap_servers=[endpoint])

    def _send_msg(self, payload):
        msg_dict = dict()
        msg_dict["agent"] = config.sen_agent

        if type(payload) == dict:
            msg_dict = {**msg_dict, **payload}
        elif type(payload) == str:
            msg_dict['msg'] = payload

        print('sending...', msg_dict)
        msg = jsonpickle.encode(msg_dict)
        kafka_producer = self._get_kafka_producer(config.sen_kafka_ep, config.sen_key_ser, config.sen_val_ser)
        if self.space is not None and self.series is not None:
            kafka_producer.send(self.space, key=self.series, value=msg)
        else:
            kafka_producer.send(config.sen_topic, key=config.sen_series, value=msg) # space, series

        # time required for kafka to get the value
        sleep(0.05)
        kafka_producer.close()


class SentinelAgentInjector: # pragma: no cover
    def __init__(self) -> None:
        super().__init__()
        # XXX consider if deployed via EPM
        # if config.esm_epm_api != "": print('WARNING: EPM is set to be used. This syslog injector does not work here.')
        self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    def _create_srv_inst_space(self, base_url, username, apikey, space=None):
        url = base_url + "/v1/api/"

        if not space:
            raise Exception('The name of the space to be created is missing')

        headers = {
            "Content-Type": "application/json",
            'x-auth-login': username,
            'x-auth-apikey': apikey
        }

        data = {"name": space}
        res = requests.post(url=url + "space/", headers=headers, data=json.dumps(data))
        res.raise_for_status()
        topic_name = res.json()['topicName']

        return topic_name

    def _setup_network(self, m, svc_id):
        # warning if more than one networks used
        if len(m.get('networks', dict()).keys()) > 1:
            print('warning - more than one network found! Selecting the first.')

        # get the name of the network
        net_name = list(m.get('networks').keys())[0]  # we get the 1st
        # find out if the network is external or not
        net_is_external = m.get('networks')[net_name].get('external', None)
        # does the network exist?
        thenet = [n for n in self.client.networks.list() if net_name == n.name]
        net_exists = (len(thenet) == 1)

        if net_is_external and not net_exists:
            raise Exception('The {net} does not exist but is declared as external'.format(net=net_name))
        elif not net_exists:
            net = self.client.networks.create(net_name, driver="bridge", labels={'creator': 'esm', 'svc_id': svc_id})
            return net
        else:
            return thenet[0]

    def _setup_logger(self, net, svc_id):

        if config.syslog_agent_sentinel_api_ep == "" or \
                config.syslog_agent_username == "" or \
                config.syslog_agent_key == "":
            raise Exception('sentinel syslog agent params are not configured')

        # topic name is returned, needed to send message on kafka
        topic_name = self._create_srv_inst_space(
            base_url=config.syslog_agent_sentinel_api_ep,
            username=config.syslog_agent_username,
            apikey=config.syslog_agent_key,
            space=svc_id
        )

        if not config.syslog_agent_sentinel_available:
            print('Syslog agent will not send to Sentinel, only receive messages without forwarding')
        if config.sen_kafka_ep == "":
            raise Exception('sentinel syslog agent params are not configured')

        syslog_agent = self.client.containers.run(
            image=config.syslog_agent_sentinel_image, detach=True,
            labels={
                'service_id': svc_id
            },
            network=net.name,
            environment=[
                 "SENTINEL_SYSLOG_SPACE_NAME={sn}".format(sn=svc_id),
                 "SENTINEL_SYSLOG_TOPIC_NAME={st}".format(st=topic_name),
                 "SENTINEL_AVAILABLE={ssla_enable}".format(ssla_enable=config.syslog_agent_sentinel_available),
                 "SENTINEL_API={sa}".format(sa=config.syslog_agent_sentinel_api_ep),
                 "SENTINEL_KAFKA_ENDPOINT={kep}".format(kep=config.sen_kafka_ep),
                 "SENTINEL_SYSLOG_USERNAME={ssu}".format(ssu=config.syslog_agent_username),
                 "SENTINEL_SYSLOG_USER_API_KEY={ssua}".format(ssua=config.syslog_agent_key),
                 "SENTINEL_SYSLOG_BIND_ADDR={ssba}".format(ssba=config.syslog_agent_bind_address),
                 "SENTINEL_SYSLOG_BIND_PORT={ssbp}".format(ssbp=config.syslog_agent_bind_port),
            ]
        )
        sysla_ip = ''
        while sysla_ip == '':  # wait - there is a delay in IP address allocation
            syslog_agent = self.client.containers.get(syslog_agent.id)
            sysla_ip = syslog_agent.attrs['NetworkSettings']['Networks'][net.name]['IPAddress']
            sleep(2)
        print("Syslog agent IP Address{}".format(sysla_ip))
        return syslog_agent

    def _update_deployment(self, m, net, syslog_agent):
        log_config = {
            'driver': 'syslog',
            'options': {
                'syslog-address': "udp://{sysla_ip}:{sysla_port}".format(sysla_ip=syslog_agent.attrs['NetworkSettings']['Networks'][net.name]['IPAddress'], sysla_port=config.syslog_agent_bind_port),
                'syslog-format': 'rfc5424'
            }
        }
        # let's do the manifest mods
        for _, srv in m['services'].items():
            srv['logging'] = log_config

        # if net is created by the ESM that network needs to be set to external
        if len(net.attrs['Labels']) > 0:
            m['networks'] = {
                net.name: {
                    'external': 'true'
                }
            }

        print(m)
        return m

    def inject(self, m_yaml, svc_id):
        net = self._setup_network(m_yaml, svc_id)
        syslog_agent = self._setup_logger(net, svc_id)
        return self._update_deployment(m_yaml, net, syslog_agent)

    def remove(self, srv_id):
        for c in self.client.containers.list(
                all=True,
                filters={
                    "label": "service_id={}".format(srv_id)
                }
        ):
            print('Removing the sentinel syslog agent {} for service id {}'.format(c.name, srv_id))
            c.remove(force=True)
