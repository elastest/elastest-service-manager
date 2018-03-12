import os
import secrets
import string

from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.exceptions import Conflict, NotFound, ValidationError
from keystoneclient.v3 import client

from adapters.log import get_logger

LOG = get_logger(__name__)

def __keystone_client():
    base_url = os.environ.get('ET_AAA_ESM_KEYSTONE_BASE_URL', '')
    base_path = os.environ.get('ET_AAA_ESM_KEYSTONE_BASE_PATH', '/v3')
    admin_port = os.environ.get('ET_AAA_ESM_KEYSTONE_ADMIN_PORT', 35357)
    username = os.environ.get('ET_AAA_ESM_KEYSTONE_USERNAME', '')
    passwd = os.environ.get('ET_AAA_ESM_KEYSTONE_PASSWD', '')
    tenant = os.environ.get('ET_AAA_ESM_KEYSTONE_TENANT', '')

    # XXX note that the domain is assumed to be default
    auth = v3.Password(auth_url=base_url + ':' + str(admin_port) + base_path, username=username, password=passwd,
                       project_name=tenant, user_domain_id="default", project_domain_id="default")
    # TODO Cache this client
    keystone = client.Client(session=session.Session(auth=auth))
    return keystone


def create_credentials(binding_id, instance_id):
    keystone = __keystone_client()

    # XXX create a domain per user or per service type?
    project_id = None
    try:
        project = keystone.projects.create(name="tenant-" + instance_id,
                                           description="this is the project for tenant-" + instance_id,
                                           domain="default", enabled=True)
        project_id = project.id
    except Conflict:
        LOG.error('Cannot create the project {name} as it exists already'.format(name="tenant-" + instance_id))

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
    except Conflict:
        LOG.error('Cannot create the user {name} as it exists already'.format(name='user-' + binding_id))

    # associate role with user and project
    role_name = os.environ.get('ET_AAA_ESM_ROLE_NAME', '_member_')
    role_id = None
    for x in keystone.roles.list():  # is there a better way to do this?
        if x.name == role_name:
            role_id = x.id
    if not role_id:
        LOG.error("The role {r_name} cannot be found. Change the environment variable ET_AAA_ESM_ROLE_NAME to a "
                  "valid role name.".format(r_name=role_name))
        raise Exception("The role {r_name} cannot be found. Change the environment variable ET_AAA_ESM_ROLE_NAME "
                        "to a valid role name.".format(r_name=role_name))

    try:
        keystone.roles.grant(role=role_id, user=user_id, project=project_id)  # idempotent
    except ValidationError:
        LOG.error('Project({p_id}), User({u_id}) or Role ({r_id}) ID is empty - this should not happen!'
                  .format(p_id=project_id, u_id=user_id, r_id=role_id))

    return {
        'auth_url': keystone.auth.api.get_endpoint(),
        'tenant': "tenant-" + instance_id,
        'tenant_id': project_id,
        'user': 'user-' + binding_id,
        'user_id': user_id,
        'password': password
    }


def delete_credentials(binding_info):
    keystone = __keystone_client()
    try:
        # note: the order is important here
        keystone.projects.delete(binding_info['tenant_id'])
        keystone.users.delete(binding_info['user_id'])
    except NotFound:
        LOG.error('Cannot delete, resource not found')
