import os
import shutil

from compose.cli.main import TopLevelCommand, project_from_options
# from kubernetes import client, config

from adapters.log import LOG
from adapters.datasource import STORE


class Backend(object):
    def create(self, instance_id, content, c_type):
        pass

    def info(self, instance_id):
        pass

    def delete(self, instance_id):
        pass


class DockerBackend(Backend):
    def __init__(self) -> None:
        super().__init__()
        self.options = {
            "--no-deps": False,
            "--abort-on-container-exit": False,  # do not set to True
            "SERVICE": "",
            "--remove-orphans": False,
            "--no-recreate": True,
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

        # TODO this location needs to be configurable
        self.manifest_cache = '/tmp'

    def create(self, instance_id, content, c_type):
        if c_type == 'docker-compose':
            LOG.warn('WARNING: this is for local-only deployments.')
            return self._create_compose(inst_id=instance_id, content=content)
        else:
            raise NotImplementedError('The type ({type}) of cluster manager is unknown'.format(type=c_type))

    def _create_compose(self, inst_id, content):
        """
        This creates a set of containers using docker compose.
        Note: the use of the docker compose python module is unsupported by docker inc.
        :param content: the docker compose file as a string
        :return:
        """

        # XXX this is a dirty hack - mongodb strips newlines!
        LOG.debug("# content = content.replace('</br>', '\\n') is a dirty hack - mongodb strips newlines!")
        content = content.replace('</br>', '\n')
        LOG.debug(content)

        # when we get the manifest, we have to dump it to a temporary file
        # to allow for multiple stack instances we need to have multiple projects!
        # this means multiple directories
        mani_dir = self.manifest_cache + '/' + inst_id

        if not os.path.exists(mani_dir):
            os.makedirs(mani_dir)
        else:
            LOG.info('The instance is already running with the following project: {mani_dir}'.format(mani_dir=mani_dir))

        LOG.debug('writing to: {compo}'.format(compo=mani_dir + '/docker-compose.yml'))
        m = open(mani_dir + '/docker-compose.yml', 'wt')
        m.write(content)
        m.close()
        project = project_from_options(mani_dir, self.options)
        cmd = TopLevelCommand(project)
        cmd.up(self.options)  # WARNING: this method can call sys.exit() but only if --abort-on-container-exit is True

    def info(self, instance_id):
        mani_dir = self.manifest_cache + '/' + instance_id

        if not os.path.exists(mani_dir):
            LOG.error('requested directory does not exist: {mani_dir}'.format(mani_dir=mani_dir))
            # TODO raise exception
            return

        LOG.debug('info from: {compo}'.format(compo=mani_dir + '/docker-compose.yml'))
        project = project_from_options(mani_dir, self.options)
        # cmd = TopLevelCommand(project)

        containers = project.containers(service_names=self.options['SERVICE'], stopped=True)

        # containers = sorted(
        #     self.project.containers(service_names=options['SERVICE'], stopped=True) +
        #     self.project.containers(service_names=options['SERVICE'], one_off=OneOffFilter.only),
        #     key=attrgetter('name'))

        # XXX questionable flattening of information - is it necessary? looks fugly...
        info = dict()
        for c in containers:
            LOG.debug('{name} container image name: {img_name}'
                      .format(name=c.name, img_name=c.image_config['RepoTags'][0]))
            info[c.name+'_image_name'] = c.image_config['RepoTags'][0]
            LOG.debug('{name} container image: {img}'.format(name=c.name, img=c.image))
            info[c.name + '_image_id'] = c.image

            LOG.debug(c.ports)

            for k, v in c.ports.items():
                if isinstance(v, list):
                    for i in v:
                        info[c.name + '_' + k + '/HostIp'] = i['HostIp']
                        info[c.name + '_' + k + '/HostPort'] = i['HostPort']
                else:
                    info[c.name + '_' + k] = v

            LOG.debug('{name} container state: {state}'.format(name=c.name, state=c.human_readable_state))
            info[c.name + '_state'] = c.human_readable_state
            LOG.debug('{name} container command: {cmd}'.format(name=c.name, cmd=c.human_readable_command))
            info[c.name + '_cmd'] = c.human_readable_command

        return info

    def delete(self, instance_id):
        mani_dir = self.manifest_cache + '/' + instance_id

        if not os.path.exists(mani_dir):
            LOG.error('requested directory does not exist: {mani_dir}'.format(mani_dir=mani_dir))
            # TODO raise exception
            return

        # TODO see if these can be moved into constructor
        self.options["--force"] = True
        self.options["--rmi"] = "none"
        LOG.info('destroying: {compo}'.format(compo=mani_dir + '/docker-compose.yml'))
        project = project_from_options(mani_dir, self.options)
        cmd = TopLevelCommand(project)
        cmd.down(self.options)
        try:
            shutil.rmtree(mani_dir)
        except PermissionError:
            # Done to let travis pass
            # TODO make location of mani_dir configurable
            LOG.warn('Could not delete the directory {dir}'.format(dir=mani_dir))


class KubernetesBackend(Backend):
    def __init__(self) -> None:
        super().__init__()
#         # self.directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
#         # prefix = "k8s_"
#         # Identify all kubernetes files to process
#         # self.files = [os.path.join(self.directory, filename) for filename in os.listdir(self.directory)
#         #               if filename.startswith(prefix) and filename.endswith(".yaml")]
#         # k8s_config_file = os.path.abspath(os.path.join(self.directory, 'k8s_config'))
#         # self.api = pykube.HTTPClient(pykube.KubeConfig.from_file(k8s_config_file))
#         config.load_kube_config()
#         self.k8s_beta = client.ExtensionsV1beta1Api()

    def create(self, instance_id, content, c_type):
        super().create(instance_id, content, c_type)
#
#         # LOG.debug("# content = content.replace('</br>', '\\n') is a dirty hack - mongodb strips newlines!")
#         # content = content.replace('</br>', '\n')
#         #
#         # dep = yaml.load(content)
#         # resp = self.k8s_beta.create_namespaced_deployment(body=dep, namespace="default")
#         # print("Deployment created. status='%s'" % str(resp.metadata.uid))
#         # print("Deployment created. status='%s'" % str(resp.status))
#         # return resp.metadata.uid

    def delete(self, instance_id):
        super().delete(instance_id)
#         # content = ''
#         # dep = yaml.load(content)
#         # resp = self.k8s_beta.delete_collection_namespaced_deployment(body=dep, namespace="default")

    def info(self, instance_id):
        super().info(instance_id)


class DummyBackend(Backend):
    def __init__(self) -> None:
        super().__init__()

    def create(self, instance_id, content, c_type):
        super().create(instance_id, content, c_type)
        LOG.info('DummyBackend driver: create called')

    def delete(self, instance_id):
        super().delete(instance_id)
        LOG.info('DummyBackend driver: delete called')

    def info(self, instance_id):
        super().info(instance_id)
        LOG.info('DummyBackend driver: info called')
        # TODO update to include the network info
        dummy_data = {
            'testid123_spark-worker_1_image_name': 'elastest/ebs-spark-base:0.5.0',
            'testid123_spark-worker_1_image_id': 'sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb',
            'testid123_spark-worker_1_state': 'Up',
            'testid123_spark-worker_1_cmd': '/usr/bin/supervisord --configuration=/opt/conf/slave.conf',
            'spark-master_image_name': 'elastest/ebs-spark-base:0.5.0',
            'spark-master_image_id': 'sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb',
            'spark-master_state': 'Up', 'spark-master_cmd': '/usr/bin/supervisord --configuration=/opt/conf/master.conf'
        }
        LOG.info('Dummy data:\n{dummy}'.format(dummy=dummy_data))
        return dummy_data


class TOSCABackend(Backend):
    def __init__(self) -> None:
        super().__init__()

    def create(self, instance_id, content, c_type):
        super().create(instance_id, content, c_type)

    def delete(self, instance_id):
        super().delete(instance_id)

    def info(self, instance_id):
        super().info(instance_id)
        return {
            'testid123_spark-worker_1_image_name': 'elastest/ebs-spark-base:0.5.0',
            'testid123_spark-worker_1_image_id':
                'sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb',
            'testid123_spark-worker_1_state': 'Up',
            'testid123_spark-worker_1_cmd': '/usr/bin/supervisord --configuration=/opt/conf/slave.conf',
            'spark-master_image_name': 'elastest/ebs-spark-base:0.5.0',
            'spark-master_image_id': 'sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb',
            'spark-master_state': 'Up', 'spark-master_cmd': '/usr/bin/supervisord --configuration=/opt/conf/master.conf'
        }


class EPM(Backend):

    def __init__(self) -> None:
        self.backends = {
            'docker': DockerBackend(),
            'kubernetes': KubernetesBackend(),
            'tosca': TOSCABackend(),
            'dummy': DummyBackend()
        }
        self.store = STORE
        # set an alias to the docker-compose driver
        LOG.info('Adding docker-compose alias to DockerBackend')
        self.backends['docker-compose'] = self.backends.get('docker')
        LOG.info('Adding k8s alias to KubernetesBackend')
        self.backends['k8s'] = self.backends.get('kubernetes')

    def create(self, instance_id: str, content: str, c_type: str):
        be = self.backends.get(c_type, self.backends['dummy'])
        be.create(instance_id, content, c_type)

    def info(self, instance_id: str):
        manifest_type = self._get_manifest_type(instance_id)
        be = self.backends.get(manifest_type, self.backends['dummy'])
        return be.info(instance_id)

    def delete(self, instance_id: str):
        manifest_type = self._get_manifest_type(instance_id)
        be = self.backends.get(manifest_type, self.backends['dummy'])
        be.delete(instance_id)

    def _get_manifest_type(self, instance_id: str) -> str:
        srv_inst = self.store.get_service_instance(instance_id=instance_id)
        mani_id = srv_inst[0].context['manifest_id']
        mani = self.store.get_manifest(manifest_id=mani_id)[0]
        return mani.manifest_type

EPM = EPM()
