import secrets
import string

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.exceptions import Conflict, NotFound, ValidationError
from keystoneclient.v3 import client

import config
from adapters.log import get_logger

LOG = get_logger(__name__)


class Auth():

    def __init__(self) -> None:
        super().__init__()

    def create_credentials(self, binding_id, instance_id):
        pass

    def delete_credentials(self, binding_info):
        pass


class DummyAuth(Auth):

    def __init__(self) -> None:
        super().__init__()

    def create_credentials(self, binding_id, instance_id):
        return {
            'auth_url': 'http://dummy.endpoint/frag',
            'tenant': "tenant-" + instance_id,
            'tenant_id': '123-123-123',
            'user': 'user-' + binding_id,
            'user_id': 'user',
            'password': 'pass'
        }

    def delete_credentials(self, binding_info):
        pass


class KeystoneAuth(Auth):  # pragma: keystone  no cover

    def create_credentials(self, binding_id, instance_id):
        keystone = self._keystone_client()

        # XXX create a domain per user or per service type?
        project_id = None
        try:
            project = keystone.projects.create(name="tenant-" + instance_id,
                                               description="this is the project for tenant-" + instance_id,
                                               domain="default", enabled=True)
            project_id = project.id
        except Conflict as c:
            LOG.error('Cannot create the project {name} as it exists already'.format(name="tenant-" + instance_id))
            raise c

        # create user
        user_id = None
        password = ''.join(
            secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(20)
        )
        try:
            user = keystone.users.create(name='user-' + binding_id, default_project=project_id, password=password,
                                         email='user@localhost',
                                         description='User with access to project: tenant-' + instance_id, enabled=True)
            user_id = user.id
        except Conflict as c:
            LOG.error('Cannot create the user {name} as it exists already'.format(name='user-' + binding_id))
            raise c

        # associate role with user and project
        role_id = None
        for x in keystone.roles.list():  # is there a better way to do this?
            if x.name == config.auth_role_name:
                role_id = x.id
        if not role_id:
            LOG.error("The role {r_name} cannot be found. Change the environment variable ET_AAA_ESM_ROLE_NAME to a "
                      "valid role name.".format(r_name=config.auth_role_name))
            raise Exception("The role {r_name} cannot be found. Change the environment variable ET_AAA_ESM_ROLE_NAME "
                            "to a valid role name.".format(r_name=config.auth_role_name))

        try:
            keystone.roles.grant(role=role_id, user=user_id, project=project_id)  # idempotent
        except ValidationError as ve:
            LOG.error('Project({p_id}), User({u_id}) or Role ({r_id}) ID is empty - this should not happen!'
                      .format(p_id=project_id, u_id=user_id, r_id=role_id))
            raise ve

        return {
            'auth_url': keystone.auth.api.get_endpoint(),
            'tenant': "tenant-" + instance_id,
            'tenant_id': project_id,
            'user': 'user-' + binding_id,
            'user_id': user_id,
            'password': password
        }

    def delete_credentials(self, binding_info):
        keystone = self._keystone_client()
        try:
            # note: the order is important here
            keystone.projects.delete(binding_info['tenant_id'])
            keystone.users.delete(binding_info['user_id'])
        except NotFound as nf:
            LOG.error('Cannot delete, resource not found')
            raise nf

    def _keystone_client(self):


        # XXX note that the domain is assumed to be default
        auth = v3.Password(auth_url=config.auth_base_url + ':' + str(config.auth_admin_port) + config.auth_base_path,
                           username=config.auth_username, password=config.auth_passwd,
                           project_name=config.auth_tenant, user_domain_id="default", project_domain_id="default")
        keystone = client.Client(session=session.Session(auth=auth))
        return keystone


if config.auth_base_url != '':
    AUTH = KeystoneAuth()
else:  # default
    AUTH = DummyAuth()