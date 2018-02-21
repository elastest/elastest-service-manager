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
import shutil
from typing import Dict
import yaml
import tarfile
import tempfile

import docker
# XXX these docker imports are internal and not supported to be used by external processes
from compose.cli.main import TopLevelCommand
from compose.cli.command import project_from_options

# from kubernetes import client, config
import adapters.log
from epm_client.apis.package_api import PackageApi
from epm_client.apis.resource_group_api import ResourceGroupApi

LOG = adapters.log.get_logger(name=__name__)


# TODO better exception handling


class DeployerBackend(object):
    def create(self, instance_id: str, content: str, c_type: str, **kwargs) -> None:
        pass

    def info(self, instance_id: str, **kwargs) -> Dict[str, str]:
        pass

    def delete(self, instance_id: str, **kwargs) -> None:
        pass

    def is_ok(self, **kwargs) -> bool:
        pass

    def _reconcile_state(self, info):
        states = set([v for k, v in info.items() if k.endswith('state')])
        # states from compose.container.Container: 'Paused', 'Restarting', 'Ghost', 'Up', 'Exit %s'
        # states for OSBA: in progress, succeeded, and failed
        for state in states:
            if state.startswith('Exit'):
                # there's been an error with docker
                info['srv_inst.state.state'] = 'failed'
                info['srv_inst.state.description'] = \
                    'There was an error in creating the instance {error}'.format(error=state)
        if len(states) == 1:  # if all states of the same value
            if states.pop() == 'Up':  # if running: Up
                info['srv_inst.state.state'] = 'succeeded'
                info['srv_inst.state.description'] = 'The service instance has been created successfully'
        else:
            # still waiting for completion
            info['srv_inst.state.state'] = 'in progress'
            info['srv_inst.state.description'] = 'The service instance is being created.'


class DockerBackend(DeployerBackend):
    def __init__(self) -> None:
        super().__init__()
        LOG.info('Adding DockerBackend')
        self.options = {
            "--no-deps": False,
            "--abort-on-container-exit": False,  # do not set to True
            "SERVICE": "",
            "--remove-orphans": False,
            "--no-recreate": True,
            "--always-recreate-deps": False,
            "--force-recreate": False,
            "--build": False,
            '--no-build': False,
            '--no-color': False,
            # "--rmi": "none",
            "--volumes": "/private",
            # "--follow": False,
            # "--timestamps": False,
            # "--tail": "all",
            "-d": True,
            "-q": False,  # quiet
            "--scale": [],  # don't need this but have to supply
        }

        self.manifest_cache = os.environ.get('ESM_TMP_DIR', tempfile.gettempdir())

    def create(self, instance_id: str, content: str, c_type: str, **kwargs) -> None:
        """
        This creates a set of containers using docker compose.
        Note: the use of the docker compose python module is unsupported by docker inc.
        :param content: the docker compose file as a string
        :return:
        """
        if c_type != 'docker-compose':
            raise NotImplementedError('The type ({type}) of cluster manager is unknown'.format(type=c_type))

        # when we get the manifest, we have to dump it to a temporary file
        # to allow for multiple stack instances we need to have multiple projects!
        # this means multiple directories
        mani_dir = self.manifest_cache + '/' + instance_id

        if not os.path.exists(mani_dir):
            os.makedirs(mani_dir)
        else:
            LOG.info('The instance is already running with the following project: {mani_dir}'.format(mani_dir=mani_dir))
            LOG.warning('Content in this directory will be overwritten.')
            # XXX shouldn't this raise an exception?

        # can supply external parameters here...
        # parameters is the name set in the OSBA spec for additional parameters supplied on provisioning
        # if none supplied, we use an empty dict
        # add optionally supplied parameters as environment variables
        parameters = kwargs.get('parameters', dict())
        if len(parameters) > 0:
            # convert dict to a list
            m = yaml.load(content)
            if 'all' in parameters and len(parameters['all']) > 0:
                LOG.warning('Common AND service specific environment variables not implemented at the moment')
                # all_env_list = self.dict_to_list(parameters['all'])

            extra_env_list = self.dict_to_list(parameters)

            # update each service's env vars
            for k, v in m['services'].items():
                if k in parameters:
                    LOG.warning('Common AND service specific environment variables not implemented at the moment')

                try:
                    # use a set to remove identical elements and convert back to a list
                    v['environment'] = list(set(v['environment'] + extra_env_list))
                    LOG.info('Updated set of environment variables for {svc} are: \n{env}'.format(svc=k, env=v['environment']))
                except KeyError:
                    LOG.warning('There is no environment variables defined for {svc}'.format(svc=k))
                    v['environment'] = extra_env_list
                    LOG.info(
                        'New set of environment variables for {svc} are: \n{env}'.format(svc=k, env=v['environment']))

            content = yaml.dump(m)

        LOG.debug('writing to: {compo}'.format(compo=mani_dir + '/docker-compose.yml'))
        m = open(mani_dir + '/docker-compose.yml', 'wt')
        m.write(content)
        m.close()

        project = project_from_options(mani_dir, self.options)
        cmd = TopLevelCommand(project)
        cmd.up(self.options)

    def dict_to_list(self, parameters):
        extra_env_list = list()
        for k, v in parameters.items():
            LOG.info('Including additional environment variables: {k}={v}'.format(k=k, v=v))
            extra_env_list.append(k + '=' + v)
        return extra_env_list

    def info(self, instance_id: str, **kwargs) -> Dict[str, str]:
        mani_dir = self.manifest_cache + '/' + instance_id

        if not os.path.exists(mani_dir):
            LOG.warning('requested directory does not exist: {mani_dir}'.format(mani_dir=mani_dir))
            return {}

        LOG.debug('info from: {compo}'.format(compo=mani_dir + '/docker-compose.yml'))
        project = project_from_options(mani_dir, self.options)
        containers = project.containers(service_names=self.options['SERVICE'], stopped=True)

        # rg = docker_handler.convert_to_resource_group(container_ids, resource_group_name=package_name)
        # for id in container_ids:
        #     container = client.containers.get(id)

        info = dict()
        for c in containers:
            # basic info...
            name = c.name
            if name.endswith('_1'): name = c.name[0:-2]
            info[name + '_image_name'] = c.image_config['RepoTags'][0]
            info[name + '_image_id'] = c.image
            info[name + '_net_name'] = c.dictionary["HostConfig"]["NetworkMode"]
            info[name + '_cmd'] = c.human_readable_command
            info[name + '_state'] = c.human_readable_state
            info = {**info, **self.container_attrs(name, c.dictionary)}

            # environment info...
            for k, v in c.environment.items():
                info[name + '_environment_' + k] = v

            # ip address info...
            # add the IP address of the container, assumes there's only 1 IP address assigned to container
            ip = [value.get('IPAddress') for value in c.dictionary['NetworkSettings']['Networks'].values()]
            info[name + '_' + 'Ip'] = ip[0]

        self._reconcile_state(info)

        LOG.debug('Stack\'s attrs:')
        LOG.debug(info)
        return info

    def container_attrs(self, name, data):
        out = dict()
        for x in data:
            self._container_attrs(name, data, [x], out)
        return out

    def _container_attrs(self, name, data, names, out):
        a = data
        for x in names:
            a = a[x]

        if isinstance(a, str):
            key = names[0]
            for n in range(1, len(names)):
                key += "_" + str(names[n])
            out[name + '_'+ key.lower()] = str(a).strip()

        if isinstance(a, list) and len(a) > 0:
            if isinstance(a[0], str):
                value = ""
                key = names[0]
                for n in range(1, len(names)):
                    key += "_" + str(names[n])
                for v in a:
                    value += v + ";"
                out[name + '_'+ key.lower()] = str(a).strip()
            else:
                key = names[0]
                for n in range(1, len(names)):
                    key += "_" + str(names[n])
                out[name + '_'+ key.lower()] = str(a).strip()

        if isinstance(a, dict):
            for n in a:
                new_names = []
                new_names.extend(names)
                new_names.append(n)
                self._container_attrs(name, data, new_names, out)

    def delete(self, instance_id: str, **kwargs) -> None:
        mani_dir = self.manifest_cache + '/' + instance_id

        if not os.path.exists(mani_dir):
            LOG.warning('requested directory does not exist: {mani_dir}'.format(mani_dir=mani_dir))
            return

        self.options["--force"] = True
        self.options["--rmi"] = "none"
        timeout = os.environ.get('ESM_DOCKER_DELETE_TIMEOUT', 20)
        self.options['--timeout'] = timeout
        LOG.info('destroying: {compo} with timeout of: {timeout}'.format(compo=mani_dir + '/docker-compose.yml',
                                                                         timeout=timeout))
        project = project_from_options(mani_dir, self.options)
        cmd = TopLevelCommand(project)
        cmd.down(self.options)

        try:
            shutil.rmtree(mani_dir)
        except PermissionError:
            # Done to let travis pass
            LOG.warning('Could not delete the directory {dir}'.format(dir=mani_dir))

    def is_ok(self, **kwargs):
        client = docker.from_env()
        # this container should be small - this is 452 bytes
        # https://github.com/DieterReuter/dockerchallenge-smallest-image
        container = client.containers.run("dieterreuter/hello", detach=True)
        if not container:
            return False
        container.remove(force=True)
        return True


class EPMBackend(DeployerBackend):
    def __init__(self) -> None:
        super().__init__()
        LOG.info('Adding EPMBackend')
        self.sid_to_rgid = dict()  # TODO make this persistent... better that this done in the caller of the method
        self.api_endpoint = os.environ.get('ET_EPM_API', 'http://localhost:8180/') + 'v1'
        LOG.info('EPM API Endpoint: ' + self.api_endpoint)

    def create(self, instance_id: str, content: str, c_type: str, **kwargs) -> None:
        super().create(instance_id, content, c_type, **kwargs)

        if c_type != 'epm':
            raise NotImplementedError('The type ({type}) of cluster manager is unknown'.format(type=c_type))

        # create the tar file including metadata.yaml and docker-compose.yaml
        dirpath = tempfile.mkdtemp()

        with open(dirpath + 'metadata.yaml', 'w') as out:
            out.write('name: ' + instance_id)

        # update parameters if they're supplied
        with open(dirpath + 'docker-compose.yaml', 'w') as out:
            out.write(content)

        with tarfile.open(dirpath + 'service.tar', mode='w') as tf:
            tf.add(dirpath + 'metadata.yaml', arcname='metadata.yaml', recursive=False)
            tf.add(dirpath + 'docker-compose.yaml', arcname='docker-compose.yml', recursive=False)

        package = PackageApi()
        package.api_client.host = self.api_endpoint

        # submit service tar to EPM
        pkg = package.receive_package(dirpath + "service.tar")

        # record the service instance ID against the resource group ID returned by EPM
        # TODO make persistent
        self.sid_to_rgid[instance_id] = pkg.to_dict()['id']

    def info(self, instance_id: str, **kwargs) -> Dict[str, str]:
        super().info(instance_id, **kwargs)
        # source: we have a resource group ID. iterate through the VDUs to return the info
        # output:
        #
        # {'id': 'ca35a24a-1016-46fa-8aa4-7d52e692867e',
        #  'name': 'test-id-123',
        #  'networks': [{'cidr': '172.23.0.0/16',
        #                'id': '81147bc2-d6b1-4be8-9a04-2d6ec3f3a712',
        #                'name': 'testid123_default',
        #                'networkId': 'c7f903db071b48dc93acb13fd91b7056733fcc4214d3063de0be6a1c6000a18c',
        #                'poPName': 'docker-local'}],
        #  'pops': [],
        #  'vdus': [{'computeId': '273e094737ee316856f089f5a464560d395b9315142af6f7a3e9e77d94adb692',
        #            'events': [],
        #            'id': '009e77d4-254a-4752-bd3f-d8bea76475d4',
        #            'imageName': 'elastest/ebs-spark:latest',
        #            'ip': '172.23.0.2',
        #            'metadata': [{'id': '43117b4b-d360-427a-92f4-89fe74e84c73',
        #                          'key': 'PORT_BINDING',
        #                          'value': '8080:8080/tcp'},
        #                         {'id': '9e9c45dc-de07-410b-933e-adfd559779d5',
        #                          'key': 'PORT_BINDING',
        #                          'value': '7077:7077/tcp'}],
        #            'name': '/spark-master',
        #            'netName': 'testid123_default',
        #            'poPName': '',
        #            'status': None},
        #           {'computeId': 'afee33cdd0a5ce2b26f262762a1ccfce89056ff0f839a0188c30c600b9f422a9',
        #            'events': [],
        #            'id': '3ed4dde7-543a-4cfe-abbc-a5352c202826',
        #            'imageName': 'elastest/ebs:latest',
        #            'ip': '172.23.0.4',
        #            'metadata': [{'id': '8dd88b81-4c15-4f2f-ac45-c00a3854a163',
        #                          'key': 'PORT_BINDING',
        #                          'value': '5000:5000/tcp'}],
        #            'name': '/testid123_rest-api_1',
        #            'netName': 'testid123_default',
        #            'poPName': '',
        #            'status': None},
        #           {'computeId': 'fbae3639bc32390844c578bf9e183f39c7fa0c63686df08aa764839908c7bcc7',
        #            'events': [],
        #            'id': '1ae0af11-ff1e-4559-a574-d826f0799a67',
        #            'imageName': 'elastest/ebs-spark:latest',
        #            'ip': '172.23.0.3',
        #            'metadata': [{'id': 'dc70c8ea-b470-4e76-bdd1-b5741a8c59d5',
        #                          'key': 'PORT_BINDING',
        #                          'value': ':8081/tcp'}],
        #            'name': '/testid123_spark-worker_1',
        #            'netName': 'testid123_default',
        #            'poPName': '',
        #            'status': None}]}
        rgrp = ResourceGroupApi()
        rgrp.api_client.host = self.api_endpoint

        # TODO better that sid_to_rgid done in the caller of the method
        epm_info = rgrp.get_resource_group_by_id(id=self.sid_to_rgid[instance_id])

        epm_info = epm_info.to_dict()
        info = dict()
        container_names = []

        for v in epm_info['vdus']:
            for mi in v['metadata']:
                # EPM prepends '/' to container names. remove this.
                name = v['name'][1:]
                # docker provides containers name postpended with '_1' however EPM does not. remove this.
                if name.endswith('_1'): name = name[0:-2]
                container_names.append(name)
                info[(name + '_' + mi['key']).lower()] = mi['value']

        # adds compat with internal docker impl.
        for name in container_names:
            info[name + '_image_name'] = info[name + '_config_image']
            info[name + '_image_id'] = info[name + '_image']
            info[name + '_net_name'] = info[name + '_hostconfig_networkmode']
            info[name + '_cmd'] = info[name + '_config_cmd']
            info[name + '_state'] = info[name + '_state_status']

            # set IP address of container as per local docker driver
            info[name + '_Ip'] = info[name + '_networksettings_networks_' +
                                      info[name + '_hostconfig_networkmode'] + '_ipaddress']

            # make environement vars the same as local docker driver
            for params in info[name + '_config_env'].split(';')[:-1]:
                pv = params.split('=')
                info[name + '_environment_' + pv[0]] = pv[1]

        self._reconcile_state(info)
        LOG.debug('Stack\'s attrs:')
        LOG.debug(info)

        return info

    def delete(self, instance_id: str, **kwargs) -> None:
        super().delete(instance_id, **kwargs)
        # delete the resource group (created by package) by ID will remove the containers
        # XXX note this is a synchronous operation... potential for proxy timeouts
        package = PackageApi()
        package.api_client.host = self.api_endpoint
        LOG.info('Deleting the package/resource group ID: ' + self.sid_to_rgid[instance_id])

        # XXX better that this done in the caller of the method
        package.delete_package(id=self.sid_to_rgid[instance_id])

    def is_ok(self, **kwargs):
        # TODO
        return True


class KubernetesBackend(DeployerBackend):
    def __init__(self) -> None:
        super().__init__()
        LOG.info('Adding KubernetesBackend')
        # self.directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
        # prefix = "k8s_"
        # Identify all kubernetes files to process
        # self.files = [os.path.join(self.directory, filename) for filename in os.listdir(self.directory)
        #               if filename.startswith(prefix) and filename.endswith(".yaml")]
        # k8s_config_file = os.path.abspath(os.path.join(self.directory, 'k8s_config'))
        # self.api = pykube.HTTPClient(pykube.KubeConfig.from_file(k8s_config_file))
        # config.load_kube_config()
        # self.k8s_beta = client.ExtensionsV1beta1Api()

    def create(self, instance_id: str, content: str, c_type: str, **kwargs) -> None:
        super().create(instance_id, content, c_type)
        # dep = yaml.load(content)
        # resp = self.k8s_beta.create_namespaced_deployment(body=dep, namespace="default")
        # print("Deployment created. status='%s'" % str(resp.metadata.uid))
        # print("Deployment created. status='%s'" % str(resp.status))
        # return resp.metadata.uid

    def info(self, instance_id: str, **kwargs) -> Dict[str, str]:
        super().info(instance_id)
        return {}

    def delete(self, instance_id: str, **kwargs) -> None:
        super().delete(instance_id)
        # content = ''
        # dep = yaml.load(content)
        # resp = self.k8s_beta.delete_collection_namespaced_deployment(body=dep, namespace="default")

    def is_ok(self, **kwargs):
        return True


class DummyBackend(DeployerBackend):
    def __init__(self) -> None:
        super().__init__()
        LOG.info('Adding DummyBackend')

    def create(self, instance_id: str, content: str, c_type: str, **kwargs) -> None:
        super().create(instance_id, content, c_type)
        LOG.info('DummyBackend driver: create called')

    def info(self, instance_id: str, **kwargs) -> Dict[str, str]:
        super().info(instance_id)
        LOG.info('DummyBackend driver: info called')

        info = {}

        if 'data_source' in kwargs:
            with open(kwargs['data_source_path'], 'r') as ds:
                import json
                info = json.load(ds)
        else:
            info = {'id': 'this_is_a_test_instance', 'manifest_id': 'test-mani', 'spark-master_Ip': '172.19.0.2', 'spark-master_apparmorprofile': '', 'spark-master_args': "['--configuration=/opt/conf/master.conf']", 'spark-master_cmd': '/usr/bin/supervisord --configuration=/opt/conf/master.conf', 'spark-master_config_cmd': "['/usr/bin/supervisord', '--configuration=/opt/conf/master.conf']", 'spark-master_config_domainname': '', 'spark-master_config_env': "['ET_ESM_API=http://esm:37005/', 'BLAH=true', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/hadoop/bin:/usr/local/hadoop/sbin:/opt/alluxio/bin:/opt/spark/bin', 'JAVA_HOME=/usr/lib/jvm/java-8-oracle', 'HADOOP_LVERSION=2.7.3', 'HADOOP_HOME=/usr/local/hadoop', 'HADOOP_OPTS=-Djava.library.path=/usr/local/hadoop/lib/native', 'SPARK_VERSION=2.1.1', 'HADOOP_VERSION=2.7', 'ALLUXIO_VERSION=1.5.0', 'ALLUXIO_HOME=/opt/alluxio', 'SPARK_HOME=/opt/spark']", 'spark-master_config_hostname': 'spark-master', 'spark-master_config_image': 'elastest/ebs-spark:latest', 'spark-master_config_labels_com.docker.compose.config-hash': '288c2de137ceadf3f2bda867ff9192545ba4f81df1d500a080c3749f2ad9b0a2', 'spark-master_config_labels_com.docker.compose.container-number': '1', 'spark-master_config_labels_com.docker.compose.oneoff': 'False', 'spark-master_config_labels_com.docker.compose.project': 'thisisatestinstance', 'spark-master_config_labels_com.docker.compose.service': 'spark-master', 'spark-master_config_labels_com.docker.compose.version': '1.18.0', 'spark-master_config_user': '', 'spark-master_config_workingdir': '', 'spark-master_created': '2018-02-21T08:57:55.1106537Z', 'spark-master_driver': 'overlay2', 'spark-master_environment_ALLUXIO_HOME': '/opt/alluxio', 'spark-master_environment_ALLUXIO_VERSION': '1.5.0', 'spark-master_environment_BLAH': 'true', 'spark-master_environment_ET_ESM_API': 'http://esm:37005/', 'spark-master_environment_HADOOP_HOME': '/usr/local/hadoop', 'spark-master_environment_HADOOP_LVERSION': '2.7.3', 'spark-master_environment_HADOOP_OPTS': '-Djava.library.path=/usr/local/hadoop/lib/native', 'spark-master_environment_HADOOP_VERSION': '2.7', 'spark-master_environment_JAVA_HOME': '/usr/lib/jvm/java-8-oracle', 'spark-master_environment_PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/hadoop/bin:/usr/local/hadoop/sbin:/opt/alluxio/bin:/opt/spark/bin', 'spark-master_environment_SPARK_HOME': '/opt/spark', 'spark-master_environment_SPARK_VERSION': '2.1.1', 'spark-master_graphdriver_data_lowerdir': '/var/lib/docker/overlay2/3aca17a25d3e084c384950ac4d85e0ca7ee1a76f2f71904b066dd9e6163c42c9-init/diff:/var/lib/docker/overlay2/aee901b87cfe266a6fbcc2caec2988705626f1617540dffd65d092e29850c5c0/diff:/var/lib/docker/overlay2/ef66bddabcb2c95c9fe8d0d0fd8f896000e722ef77b87e51c65cd3400750d232/diff:/var/lib/docker/overlay2/9901effecfa02c55391434d5672dc56c3e0afaa34fe068b6bec3e83354dc6c12/diff:/var/lib/docker/overlay2/8f9c02df38e423cbca5454fc3e71d9978426625b7856faa232c83ef37fe407cd/diff:/var/lib/docker/overlay2/0643d7edf676a938afff55d3148e70ddb4894f608c6207a848e76d4c23eac00f/diff:/var/lib/docker/overlay2/9bd2d5ef6ff7d6bbf6212e44f78f61995e63c9741656ab60dc2d5aeefc452433/diff:/var/lib/docker/overlay2/853b96fb22fa5e6bd880aaeff68698f0fb709b1ac6d091182229aba935cc3e7b/diff:/var/lib/docker/overlay2/5c405326d3ee180a0b9f7870049edc6b45a78816be3115a24c2c0605cda11359/diff:/var/lib/docker/overlay2/ffbd2a5e923375de1942587d908872f195353474405404d0a923226791316fa4/diff:/var/lib/docker/overlay2/2d6d962d99b3bf1c908c50be23379ac6a6d229403da848a4248cb765e1a4a58f/diff:/var/lib/docker/overlay2/2a25b3b83eaea03ac05f5c6365c3b3d9a12188bfcb229994dde9125793676422/diff:/var/lib/docker/overlay2/b105d3fbe21decd0c84abfc0a8704849662d4f94ae36154479c99c099a272359/diff:/var/lib/docker/overlay2/d69cf46ab3eafbce6f6b56d7c717ff68c1b596482b73fd2147da6cc4b8e483e2/diff:/var/lib/docker/overlay2/2b70e94dbee7c78c727e97b7c390561874dca07c53d26db01609154f9aeb4e0d/diff:/var/lib/docker/overlay2/5f5895dc72725af494f90c5601d907a063b3411a841aa620916156ef2a1b67ef/diff:/var/lib/docker/overlay2/54cc7702f36679bb381e7f67614a2a503a9df4e8377a808bb06de9cb4e8a9206/diff', 'spark-master_graphdriver_data_mergeddir': '/var/lib/docker/overlay2/3aca17a25d3e084c384950ac4d85e0ca7ee1a76f2f71904b066dd9e6163c42c9/merged', 'spark-master_graphdriver_data_upperdir': '/var/lib/docker/overlay2/3aca17a25d3e084c384950ac4d85e0ca7ee1a76f2f71904b066dd9e6163c42c9/diff', 'spark-master_graphdriver_data_workdir': '/var/lib/docker/overlay2/3aca17a25d3e084c384950ac4d85e0ca7ee1a76f2f71904b066dd9e6163c42c9/work', 'spark-master_graphdriver_name': 'overlay2', 'spark-master_hostconfig_binds': "['/tmp/this_is_a_test_instance/spark/hadoop_conf:/usr/local/hadoop/etc/hadoop:rw', '/tmp/this_is_a_test_instance/spark/spark_conf:/opt/spark/conf:rw', '/tmp/this_is_a_test_instance/spark/alluxio_conf:/opt/alluxio/conf:rw']", 'spark-master_hostconfig_cgroup': '', 'spark-master_hostconfig_cgroupparent': '', 'spark-master_hostconfig_consolesize': '[0, 0]', 'spark-master_hostconfig_containeridfile': '', 'spark-master_hostconfig_cpusetcpus': '', 'spark-master_hostconfig_cpusetmems': '', 'spark-master_hostconfig_ipcmode': 'shareable', 'spark-master_hostconfig_isolation': '', 'spark-master_hostconfig_logconfig_type': 'json-file', 'spark-master_hostconfig_networkmode': 'thisisatestinstance_default', 'spark-master_hostconfig_pidmode': '', 'spark-master_hostconfig_portbindings_7077/tcp': "[{'HostIp': '', 'HostPort': '7077'}]", 'spark-master_hostconfig_portbindings_8080/tcp': "[{'HostIp': '', 'HostPort': '8080'}]", 'spark-master_hostconfig_restartpolicy_name': '', 'spark-master_hostconfig_runtime': 'runc', 'spark-master_hostconfig_usernsmode': '', 'spark-master_hostconfig_utsmode': '', 'spark-master_hostconfig_volumedriver': '', 'spark-master_hostnamepath': '/var/lib/docker/containers/c600ba91f469f6ebdd3a4a89b4819d3357d15adb2cbb555af6b5c2886e4ec7aa/hostname', 'spark-master_hostspath': '/var/lib/docker/containers/c600ba91f469f6ebdd3a4a89b4819d3357d15adb2cbb555af6b5c2886e4ec7aa/hosts', 'spark-master_id': 'c600ba91f469f6ebdd3a4a89b4819d3357d15adb2cbb555af6b5c2886e4ec7aa', 'spark-master_image': 'sha256:fc5a8746d0b2e6e62e55f71fc602116dac490dd549fce6d6cc6345a2e13650fd', 'spark-master_image_id': 'sha256:fc5a8746d0b2e6e62e55f71fc602116dac490dd549fce6d6cc6345a2e13650fd', 'spark-master_image_name': 'elastest/ebs-spark:latest', 'spark-master_logpath': '/var/lib/docker/containers/c600ba91f469f6ebdd3a4a89b4819d3357d15adb2cbb555af6b5c2886e4ec7aa/c600ba91f469f6ebdd3a4a89b4819d3357d15adb2cbb555af6b5c2886e4ec7aa-json.log', 'spark-master_mountlabel': '', 'spark-master_mounts': "[{'Type': 'bind', 'Source': '/tmp/this_is_a_test_instance/spark/hadoop_conf', 'Destination': '/usr/local/hadoop/etc/hadoop', 'Mode': 'rw', 'RW': True, 'Propagation': 'rprivate'}, {'Type': 'bind', 'Source': '/tmp/this_is_a_test_instance/spark/spark_conf', 'Destination': '/opt/spark/conf', 'Mode': 'rw', 'RW': True, 'Propagation': 'rprivate'}, {'Type': 'bind', 'Source': '/tmp/this_is_a_test_instance/spark/alluxio_conf', 'Destination': '/opt/alluxio/conf', 'Mode': 'rw', 'RW': True, 'Propagation': 'rprivate'}]", 'spark-master_name': '/spark-master', 'spark-master_net_name': 'thisisatestinstance_default', 'spark-master_networksettings_bridge': '', 'spark-master_networksettings_endpointid': '', 'spark-master_networksettings_gateway': '', 'spark-master_networksettings_globalipv6address': '', 'spark-master_networksettings_ipaddress': '', 'spark-master_networksettings_ipv6gateway': '', 'spark-master_networksettings_linklocalipv6address': '', 'spark-master_networksettings_macaddress': '', 'spark-master_networksettings_networks_thisisatestinstance_default_aliases': "['spark-master', 'c600ba91f469']", 'spark-master_networksettings_networks_thisisatestinstance_default_endpointid': 'd4e1465e0fb7bb66d7f4ef5861f8ec7321a2371c5ff345583445aae546963042', 'spark-master_networksettings_networks_thisisatestinstance_default_gateway': '172.19.0.1', 'spark-master_networksettings_networks_thisisatestinstance_default_globalipv6address': '', 'spark-master_networksettings_networks_thisisatestinstance_default_ipaddress': '172.19.0.2', 'spark-master_networksettings_networks_thisisatestinstance_default_ipv6gateway': '', 'spark-master_networksettings_networks_thisisatestinstance_default_macaddress': '02:42:ac:13:00:02', 'spark-master_networksettings_networks_thisisatestinstance_default_networkid': '88abef28f3a6a04803ceeab31c7b6aff12c0117d490a0219b7e0f33d2d41b5bf', 'spark-master_networksettings_ports_7077/tcp': "[{'HostIp': '0.0.0.0', 'HostPort': '7077'}]", 'spark-master_networksettings_ports_8080/tcp': "[{'HostIp': '0.0.0.0', 'HostPort': '8080'}]", 'spark-master_networksettings_sandboxid': 'f2ce15dbeaa3878f473afdd2afaee6e4e76a508c6945926cc630e9ce77903c0c', 'spark-master_networksettings_sandboxkey': '/var/run/docker/netns/f2ce15dbeaa3', 'spark-master_path': '/usr/bin/supervisord', 'spark-master_platform': 'linux', 'spark-master_processlabel': '', 'spark-master_resolvconfpath': '/var/lib/docker/containers/c600ba91f469f6ebdd3a4a89b4819d3357d15adb2cbb555af6b5c2886e4ec7aa/resolv.conf', 'spark-master_state': 'Up', 'spark-master_state_error': '', 'spark-master_state_finishedat': '0001-01-01T00:00:00Z', 'spark-master_state_startedat': '2018-02-21T08:57:55.850102Z', 'spark-master_state_status': 'running', 'thisisatestinstance_rest-api_Ip': '', 'thisisatestinstance_rest-api_apparmorprofile': '', 'thisisatestinstance_rest-api_args': "['/app/src/runebs.py']", 'thisisatestinstance_rest-api_cmd': '/usr/bin/python /app/src/runebs.py', 'thisisatestinstance_rest-api_config_cmd': "['/usr/bin/python', '/app/src/runebs.py']", 'thisisatestinstance_rest-api_config_domainname': '', 'thisisatestinstance_rest-api_config_env': "['ET_ESM_API=http://esm:37005/', 'EBS_SPARK_MASTER_URL=http://spark-master:8080/', 'EBS_PORT=5000', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin']", 'thisisatestinstance_rest-api_config_hostname': '7deed56edd36', 'thisisatestinstance_rest-api_config_image': 'elastest/ebs:latest', 'thisisatestinstance_rest-api_config_labels_com.docker.compose.config-hash': '4dea09d7915ce82100807c4019c6f291c0d635f102116b8bc7dc83e80531dd53', 'thisisatestinstance_rest-api_config_labels_com.docker.compose.container-number': '1', 'thisisatestinstance_rest-api_config_labels_com.docker.compose.oneoff': 'False', 'thisisatestinstance_rest-api_config_labels_com.docker.compose.project': 'thisisatestinstance', 'thisisatestinstance_rest-api_config_labels_com.docker.compose.service': 'rest-api', 'thisisatestinstance_rest-api_config_labels_com.docker.compose.version': '1.18.0', 'thisisatestinstance_rest-api_config_labels_description': 'Builds the Elastest Bigdata service docker image.', 'thisisatestinstance_rest-api_config_labels_maintainer': 's.gioldasis@gmail.com', 'thisisatestinstance_rest-api_config_labels_version': '0.1.0', 'thisisatestinstance_rest-api_config_user': '', 'thisisatestinstance_rest-api_config_workingdir': '/app', 'thisisatestinstance_rest-api_created': '2018-02-21T08:57:55.9278848Z', 'thisisatestinstance_rest-api_driver': 'overlay2', 'thisisatestinstance_rest-api_environment_EBS_PORT': '5000', 'thisisatestinstance_rest-api_environment_EBS_SPARK_MASTER_URL': 'http://spark-master:8080/', 'thisisatestinstance_rest-api_environment_ET_ESM_API': 'http://esm:37005/', 'thisisatestinstance_rest-api_environment_PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', 'thisisatestinstance_rest-api_graphdriver_data_lowerdir': '/var/lib/docker/overlay2/f5f62943e253d5e8f4e24f50938344c8963c2dc0bd07b45e107f687b2afcbd77-init/diff:/var/lib/docker/overlay2/952c479ecca44323f2b162bc7ac3604324de0f77700519d6f4f18ad1e8286fbe/diff:/var/lib/docker/overlay2/b8fb21782b2fb5a0b73047f838eb832cdbaa1fc1edef7a5768201bd3c0d28324/diff:/var/lib/docker/overlay2/8a6a0288bcd6f3d3c4ad2b269c7ec165cdb9675c3513d12c82938a93bde0781b/diff:/var/lib/docker/overlay2/c0c81cc6f432019168aa23427f8c750e755e68ef123aa4760d778897311197ec/diff', 'thisisatestinstance_rest-api_graphdriver_data_mergeddir': '/var/lib/docker/overlay2/f5f62943e253d5e8f4e24f50938344c8963c2dc0bd07b45e107f687b2afcbd77/merged', 'thisisatestinstance_rest-api_graphdriver_data_upperdir': '/var/lib/docker/overlay2/f5f62943e253d5e8f4e24f50938344c8963c2dc0bd07b45e107f687b2afcbd77/diff', 'thisisatestinstance_rest-api_graphdriver_data_workdir': '/var/lib/docker/overlay2/f5f62943e253d5e8f4e24f50938344c8963c2dc0bd07b45e107f687b2afcbd77/work', 'thisisatestinstance_rest-api_graphdriver_name': 'overlay2', 'thisisatestinstance_rest-api_hostconfig_binds': "['/tmp/this_is_a_test_instance/rest-api:/app:rw']", 'thisisatestinstance_rest-api_hostconfig_cgroup': '', 'thisisatestinstance_rest-api_hostconfig_cgroupparent': '', 'thisisatestinstance_rest-api_hostconfig_consolesize': '[0, 0]', 'thisisatestinstance_rest-api_hostconfig_containeridfile': '', 'thisisatestinstance_rest-api_hostconfig_cpusetcpus': '', 'thisisatestinstance_rest-api_hostconfig_cpusetmems': '', 'thisisatestinstance_rest-api_hostconfig_ipcmode': 'shareable', 'thisisatestinstance_rest-api_hostconfig_isolation': '', 'thisisatestinstance_rest-api_hostconfig_logconfig_type': 'json-file', 'thisisatestinstance_rest-api_hostconfig_networkmode': 'thisisatestinstance_default', 'thisisatestinstance_rest-api_hostconfig_pidmode': '', 'thisisatestinstance_rest-api_hostconfig_portbindings_5000/tcp': "[{'HostIp': '', 'HostPort': '5000'}]", 'thisisatestinstance_rest-api_hostconfig_restartpolicy_name': '', 'thisisatestinstance_rest-api_hostconfig_runtime': 'runc', 'thisisatestinstance_rest-api_hostconfig_usernsmode': '', 'thisisatestinstance_rest-api_hostconfig_utsmode': '', 'thisisatestinstance_rest-api_hostconfig_volumedriver': '', 'thisisatestinstance_rest-api_hostnamepath': '/var/lib/docker/containers/7deed56edd360b503251ff1383c07b1249c16bc4d63da09878a7f2ddcdd5e96e/hostname', 'thisisatestinstance_rest-api_hostspath': '/var/lib/docker/containers/7deed56edd360b503251ff1383c07b1249c16bc4d63da09878a7f2ddcdd5e96e/hosts', 'thisisatestinstance_rest-api_id': '7deed56edd360b503251ff1383c07b1249c16bc4d63da09878a7f2ddcdd5e96e', 'thisisatestinstance_rest-api_image': 'sha256:8e9e7ee1bace70f515c1c7fbe92d2cad54812e150ca09c66d7f090d56261d5e6', 'thisisatestinstance_rest-api_image_id': 'sha256:8e9e7ee1bace70f515c1c7fbe92d2cad54812e150ca09c66d7f090d56261d5e6', 'thisisatestinstance_rest-api_image_name': 'elastest/ebs:latest', 'thisisatestinstance_rest-api_logpath': '/var/lib/docker/containers/7deed56edd360b503251ff1383c07b1249c16bc4d63da09878a7f2ddcdd5e96e/7deed56edd360b503251ff1383c07b1249c16bc4d63da09878a7f2ddcdd5e96e-json.log', 'thisisatestinstance_rest-api_mountlabel': '', 'thisisatestinstance_rest-api_mounts': "[{'Type': 'bind', 'Source': '/tmp/this_is_a_test_instance/rest-api', 'Destination': '/app', 'Mode': 'rw', 'RW': True, 'Propagation': 'rprivate'}]", 'thisisatestinstance_rest-api_name': '/thisisatestinstance_rest-api_1', 'thisisatestinstance_rest-api_net_name': 'thisisatestinstance_default', 'thisisatestinstance_rest-api_networksettings_bridge': '', 'thisisatestinstance_rest-api_networksettings_endpointid': '', 'thisisatestinstance_rest-api_networksettings_gateway': '', 'thisisatestinstance_rest-api_networksettings_globalipv6address': '', 'thisisatestinstance_rest-api_networksettings_ipaddress': '', 'thisisatestinstance_rest-api_networksettings_ipv6gateway': '', 'thisisatestinstance_rest-api_networksettings_linklocalipv6address': '', 'thisisatestinstance_rest-api_networksettings_macaddress': '', 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_aliases': "['rest-api', '7deed56edd36']", 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_endpointid': '', 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_gateway': '', 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_globalipv6address': '', 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_ipaddress': '', 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_ipv6gateway': '', 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_links': "['spark-master:spark-master']", 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_macaddress': '', 'thisisatestinstance_rest-api_networksettings_networks_thisisatestinstance_default_networkid': '88abef28f3a6a04803ceeab31c7b6aff12c0117d490a0219b7e0f33d2d41b5bf', 'thisisatestinstance_rest-api_networksettings_sandboxid': '134e451ebf8171705232ddcc64dbd1f26bd4bf94fccc01cc171c18ba3fb51a69', 'thisisatestinstance_rest-api_networksettings_sandboxkey': '/var/run/docker/netns/134e451ebf81', 'thisisatestinstance_rest-api_path': '/usr/bin/python', 'thisisatestinstance_rest-api_platform': 'linux', 'thisisatestinstance_rest-api_processlabel': '', 'thisisatestinstance_rest-api_resolvconfpath': '/var/lib/docker/containers/7deed56edd360b503251ff1383c07b1249c16bc4d63da09878a7f2ddcdd5e96e/resolv.conf', 'thisisatestinstance_rest-api_state': 'Exit 2', 'thisisatestinstance_rest-api_state_error': '', 'thisisatestinstance_rest-api_state_finishedat': '2018-02-21T08:57:57.897629Z', 'thisisatestinstance_rest-api_state_startedat': '2018-02-21T08:57:57.7867037Z', 'thisisatestinstance_rest-api_state_status': 'exited', 'thisisatestinstance_spark-worker_Ip': '172.19.0.3', 'thisisatestinstance_spark-worker_apparmorprofile': '', 'thisisatestinstance_spark-worker_args': "['--configuration=/opt/conf/slave.conf']", 'thisisatestinstance_spark-worker_cmd': '/usr/bin/supervisord --configuration=/opt/conf/slave.conf', 'thisisatestinstance_spark-worker_config_cmd': "['/usr/bin/supervisord', '--configuration=/opt/conf/slave.conf']", 'thisisatestinstance_spark-worker_config_domainname': '', 'thisisatestinstance_spark-worker_config_env': "['ET_ESM_API=http://esm:37005/', 'PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/hadoop/bin:/usr/local/hadoop/sbin:/opt/alluxio/bin:/opt/spark/bin', 'JAVA_HOME=/usr/lib/jvm/java-8-oracle', 'HADOOP_LVERSION=2.7.3', 'HADOOP_HOME=/usr/local/hadoop', 'HADOOP_OPTS=-Djava.library.path=/usr/local/hadoop/lib/native', 'SPARK_VERSION=2.1.1', 'HADOOP_VERSION=2.7', 'ALLUXIO_VERSION=1.5.0', 'ALLUXIO_HOME=/opt/alluxio', 'SPARK_HOME=/opt/spark']", 'thisisatestinstance_spark-worker_config_hostname': '2ad42fa7143e', 'thisisatestinstance_spark-worker_config_image': 'elastest/ebs-spark:latest', 'thisisatestinstance_spark-worker_config_labels_com.docker.compose.config-hash': '8d2703f71ff3052cc44093607f032163fa2e22e7609876e96635b22d160fd676', 'thisisatestinstance_spark-worker_config_labels_com.docker.compose.container-number': '1', 'thisisatestinstance_spark-worker_config_labels_com.docker.compose.oneoff': 'False', 'thisisatestinstance_spark-worker_config_labels_com.docker.compose.project': 'thisisatestinstance', 'thisisatestinstance_spark-worker_config_labels_com.docker.compose.service': 'spark-worker', 'thisisatestinstance_spark-worker_config_labels_com.docker.compose.version': '1.18.0', 'thisisatestinstance_spark-worker_config_user': '', 'thisisatestinstance_spark-worker_config_workingdir': '', 'thisisatestinstance_spark-worker_created': '2018-02-21T08:57:55.9155092Z', 'thisisatestinstance_spark-worker_driver': 'overlay2', 'thisisatestinstance_spark-worker_environment_ALLUXIO_HOME': '/opt/alluxio', 'thisisatestinstance_spark-worker_environment_ALLUXIO_VERSION': '1.5.0', 'thisisatestinstance_spark-worker_environment_ET_ESM_API': 'http://esm:37005/', 'thisisatestinstance_spark-worker_environment_HADOOP_HOME': '/usr/local/hadoop', 'thisisatestinstance_spark-worker_environment_HADOOP_LVERSION': '2.7.3', 'thisisatestinstance_spark-worker_environment_HADOOP_OPTS': '-Djava.library.path=/usr/local/hadoop/lib/native', 'thisisatestinstance_spark-worker_environment_HADOOP_VERSION': '2.7', 'thisisatestinstance_spark-worker_environment_JAVA_HOME': '/usr/lib/jvm/java-8-oracle', 'thisisatestinstance_spark-worker_environment_PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/local/hadoop/bin:/usr/local/hadoop/sbin:/opt/alluxio/bin:/opt/spark/bin', 'thisisatestinstance_spark-worker_environment_SPARK_HOME': '/opt/spark', 'thisisatestinstance_spark-worker_environment_SPARK_VERSION': '2.1.1', 'thisisatestinstance_spark-worker_graphdriver_data_lowerdir': '/var/lib/docker/overlay2/3bf7ca9d96be710b3e89eb9fdb8aa3e482d2468870eb7c2ed30718a63a5c5d9b-init/diff:/var/lib/docker/overlay2/aee901b87cfe266a6fbcc2caec2988705626f1617540dffd65d092e29850c5c0/diff:/var/lib/docker/overlay2/ef66bddabcb2c95c9fe8d0d0fd8f896000e722ef77b87e51c65cd3400750d232/diff:/var/lib/docker/overlay2/9901effecfa02c55391434d5672dc56c3e0afaa34fe068b6bec3e83354dc6c12/diff:/var/lib/docker/overlay2/8f9c02df38e423cbca5454fc3e71d9978426625b7856faa232c83ef37fe407cd/diff:/var/lib/docker/overlay2/0643d7edf676a938afff55d3148e70ddb4894f608c6207a848e76d4c23eac00f/diff:/var/lib/docker/overlay2/9bd2d5ef6ff7d6bbf6212e44f78f61995e63c9741656ab60dc2d5aeefc452433/diff:/var/lib/docker/overlay2/853b96fb22fa5e6bd880aaeff68698f0fb709b1ac6d091182229aba935cc3e7b/diff:/var/lib/docker/overlay2/5c405326d3ee180a0b9f7870049edc6b45a78816be3115a24c2c0605cda11359/diff:/var/lib/docker/overlay2/ffbd2a5e923375de1942587d908872f195353474405404d0a923226791316fa4/diff:/var/lib/docker/overlay2/2d6d962d99b3bf1c908c50be23379ac6a6d229403da848a4248cb765e1a4a58f/diff:/var/lib/docker/overlay2/2a25b3b83eaea03ac05f5c6365c3b3d9a12188bfcb229994dde9125793676422/diff:/var/lib/docker/overlay2/b105d3fbe21decd0c84abfc0a8704849662d4f94ae36154479c99c099a272359/diff:/var/lib/docker/overlay2/d69cf46ab3eafbce6f6b56d7c717ff68c1b596482b73fd2147da6cc4b8e483e2/diff:/var/lib/docker/overlay2/2b70e94dbee7c78c727e97b7c390561874dca07c53d26db01609154f9aeb4e0d/diff:/var/lib/docker/overlay2/5f5895dc72725af494f90c5601d907a063b3411a841aa620916156ef2a1b67ef/diff:/var/lib/docker/overlay2/54cc7702f36679bb381e7f67614a2a503a9df4e8377a808bb06de9cb4e8a9206/diff', 'thisisatestinstance_spark-worker_graphdriver_data_mergeddir': '/var/lib/docker/overlay2/3bf7ca9d96be710b3e89eb9fdb8aa3e482d2468870eb7c2ed30718a63a5c5d9b/merged', 'thisisatestinstance_spark-worker_graphdriver_data_upperdir': '/var/lib/docker/overlay2/3bf7ca9d96be710b3e89eb9fdb8aa3e482d2468870eb7c2ed30718a63a5c5d9b/diff', 'thisisatestinstance_spark-worker_graphdriver_data_workdir': '/var/lib/docker/overlay2/3bf7ca9d96be710b3e89eb9fdb8aa3e482d2468870eb7c2ed30718a63a5c5d9b/work', 'thisisatestinstance_spark-worker_graphdriver_name': 'overlay2', 'thisisatestinstance_spark-worker_hostconfig_binds': "['/tmp/this_is_a_test_instance/spark/hadoop_conf:/usr/local/hadoop/etc/hadoop:rw', '/tmp/this_is_a_test_instance/spark/spark_conf:/opt/spark/conf:rw', '/tmp/this_is_a_test_instance/spark/alluxio_conf:/opt/alluxio/conf:rw']", 'thisisatestinstance_spark-worker_hostconfig_cgroup': '', 'thisisatestinstance_spark-worker_hostconfig_cgroupparent': '', 'thisisatestinstance_spark-worker_hostconfig_consolesize': '[0, 0]', 'thisisatestinstance_spark-worker_hostconfig_containeridfile': '', 'thisisatestinstance_spark-worker_hostconfig_cpusetcpus': '', 'thisisatestinstance_spark-worker_hostconfig_cpusetmems': '', 'thisisatestinstance_spark-worker_hostconfig_ipcmode': 'shareable', 'thisisatestinstance_spark-worker_hostconfig_isolation': '', 'thisisatestinstance_spark-worker_hostconfig_logconfig_type': 'json-file', 'thisisatestinstance_spark-worker_hostconfig_networkmode': 'thisisatestinstance_default', 'thisisatestinstance_spark-worker_hostconfig_pidmode': '', 'thisisatestinstance_spark-worker_hostconfig_portbindings_8081/tcp': "[{'HostIp': '', 'HostPort': ''}]", 'thisisatestinstance_spark-worker_hostconfig_restartpolicy_name': '', 'thisisatestinstance_spark-worker_hostconfig_runtime': 'runc', 'thisisatestinstance_spark-worker_hostconfig_usernsmode': '', 'thisisatestinstance_spark-worker_hostconfig_utsmode': '', 'thisisatestinstance_spark-worker_hostconfig_volumedriver': '', 'thisisatestinstance_spark-worker_hostnamepath': '/var/lib/docker/containers/2ad42fa7143e108e9f8659759e82ddf2227ef45a8ed50d642d70bead6924461e/hostname', 'thisisatestinstance_spark-worker_hostspath': '/var/lib/docker/containers/2ad42fa7143e108e9f8659759e82ddf2227ef45a8ed50d642d70bead6924461e/hosts', 'thisisatestinstance_spark-worker_id': '2ad42fa7143e108e9f8659759e82ddf2227ef45a8ed50d642d70bead6924461e', 'thisisatestinstance_spark-worker_image': 'sha256:fc5a8746d0b2e6e62e55f71fc602116dac490dd549fce6d6cc6345a2e13650fd', 'thisisatestinstance_spark-worker_image_id': 'sha256:fc5a8746d0b2e6e62e55f71fc602116dac490dd549fce6d6cc6345a2e13650fd', 'thisisatestinstance_spark-worker_image_name': 'elastest/ebs-spark:latest', 'thisisatestinstance_spark-worker_logpath': '/var/lib/docker/containers/2ad42fa7143e108e9f8659759e82ddf2227ef45a8ed50d642d70bead6924461e/2ad42fa7143e108e9f8659759e82ddf2227ef45a8ed50d642d70bead6924461e-json.log', 'thisisatestinstance_spark-worker_mountlabel': '', 'thisisatestinstance_spark-worker_mounts': "[{'Type': 'bind', 'Source': '/tmp/this_is_a_test_instance/spark/hadoop_conf', 'Destination': '/usr/local/hadoop/etc/hadoop', 'Mode': 'rw', 'RW': True, 'Propagation': 'rprivate'}, {'Type': 'bind', 'Source': '/tmp/this_is_a_test_instance/spark/spark_conf', 'Destination': '/opt/spark/conf', 'Mode': 'rw', 'RW': True, 'Propagation': 'rprivate'}, {'Type': 'bind', 'Source': '/tmp/this_is_a_test_instance/spark/alluxio_conf', 'Destination': '/opt/alluxio/conf', 'Mode': 'rw', 'RW': True, 'Propagation': 'rprivate'}]", 'thisisatestinstance_spark-worker_name': '/thisisatestinstance_spark-worker_1', 'thisisatestinstance_spark-worker_net_name': 'thisisatestinstance_default', 'thisisatestinstance_spark-worker_networksettings_bridge': '', 'thisisatestinstance_spark-worker_networksettings_endpointid': '', 'thisisatestinstance_spark-worker_networksettings_gateway': '', 'thisisatestinstance_spark-worker_networksettings_globalipv6address': '', 'thisisatestinstance_spark-worker_networksettings_ipaddress': '', 'thisisatestinstance_spark-worker_networksettings_ipv6gateway': '', 'thisisatestinstance_spark-worker_networksettings_linklocalipv6address': '', 'thisisatestinstance_spark-worker_networksettings_macaddress': '', 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_aliases': "['spark-worker', '2ad42fa7143e']", 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_endpointid': '78232aae15225c99d113a19a4f82aefcdef1acb6151796ac419d27fe6529240e', 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_gateway': '172.19.0.1', 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_globalipv6address': '', 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_ipaddress': '172.19.0.3', 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_ipv6gateway': '', 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_macaddress': '02:42:ac:13:00:03', 'thisisatestinstance_spark-worker_networksettings_networks_thisisatestinstance_default_networkid': '88abef28f3a6a04803ceeab31c7b6aff12c0117d490a0219b7e0f33d2d41b5bf', 'thisisatestinstance_spark-worker_networksettings_ports_8081/tcp': "[{'HostIp': '0.0.0.0', 'HostPort': '32800'}]", 'thisisatestinstance_spark-worker_networksettings_sandboxid': 'a5649b2ef74bda45bab293cf86ceb68fb0fed4d908097153fb787dc8976f8702', 'thisisatestinstance_spark-worker_networksettings_sandboxkey': '/var/run/docker/netns/a5649b2ef74b', 'thisisatestinstance_spark-worker_path': '/usr/bin/supervisord', 'thisisatestinstance_spark-worker_platform': 'linux', 'thisisatestinstance_spark-worker_processlabel': '', 'thisisatestinstance_spark-worker_resolvconfpath': '/var/lib/docker/containers/2ad42fa7143e108e9f8659759e82ddf2227ef45a8ed50d642d70bead6924461e/resolv.conf', 'thisisatestinstance_spark-worker_state': 'Up', 'thisisatestinstance_spark-worker_state_error': '', 'thisisatestinstance_spark-worker_state_finishedat': '0001-01-01T00:00:00Z', 'thisisatestinstance_spark-worker_state_startedat': '2018-02-21T08:57:56.7100622Z', 'thisisatestinstance_spark-worker_state_status': 'running'}

        self._reconcile_state(info)

        LOG.info('Dummy data:\n{dummy}'.format(dummy=info))
        return info

    def delete(self, instance_id: str, **kwargs) -> None:
        super().delete(instance_id)
        LOG.info('DummyBackend driver: delete called')

    def is_ok(self, **kwargs):
        # all in-memory so no more logic needed
        return True


class ResourceManager(DeployerBackend):

    def __init__(self) -> None:
        self.backends = {
            'docker': DockerBackend(),
            'kubernetes': KubernetesBackend(),
            'dummy': DummyBackend(),
            'epm': EPMBackend(),
        }
        # set an alias to the docker-compose driver
        LOG.info('Adding docker-compose alias to DockerBackend')
        self.backends['docker-compose'] = self.backends.get('docker')
        LOG.info('Adding k8s alias to KubernetesBackend')
        self.backends['k8s'] = self.backends.get('kubernetes')

    def create(self, instance_id: str, content: str, c_type: str, **kwargs):
        be = self.backends.get(c_type, self.backends['dummy'])
        be.create(instance_id, content, c_type, **kwargs)

    def info(self, instance_id: str, **kwargs) -> Dict[str, str]:
        if 'manifest_type' in kwargs:
            manifest_type = kwargs.get('manifest_type', 'dummy')
            be = self.backends.get(manifest_type, self.backends['dummy'])
        else:
            raise RuntimeError('manifest_type parameter not specified in call to info()')

        return be.info(instance_id, **kwargs)

    def delete(self, instance_id: str, **kwargs):
        if 'manifest_type' in kwargs:
            manifest_type = kwargs.get('manifest_type', 'dummy')
            be = self.backends.get(manifest_type, self.backends['dummy'])
        else:
            raise RuntimeError('manifest_type parameter not specified in call to info()')

        be.delete(instance_id, **kwargs)

    def is_ok(self, **kwargs):
        if 'manifest_type' in kwargs:
            manifest_type = kwargs.get('manifest_type', 'dummy')
            be = self.backends.get(manifest_type, self.backends['dummy'])
        else:
            ok = True
            for _, be in self.backends.items():
                if be.is_ok() != ok:
                    return False


RM = ResourceManager()
