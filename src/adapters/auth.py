import adapters.log


LOG = adapters.log.get_logger(name=__name__)


class NOPMiddleWare(object):
    """Simple WSGI middleware"""

    def __init__(self, app):
        self.app = app
        LOG.info("Using default NOP Auth. It does nothing!")
        print("Using default NOP Auth. It does nothing!")

    def __call__(self, environ, start_response):
        LOG.debug("something you want done in every http request")
        return self.app(environ, start_response)


class KeystoneMiddleware(object):

    # docker run --name keystone --hostname keystone -e ADMIN_PASSWORD=1234 --link some-mysql:mysql -p 5000:5000 -p 35357:35357  -d dizz/openstack-keystone
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        # make a call to keystone.tokens.validate(token=token)
        # from keystoneauth1.identity import v3
        # from keystoneauth1 import session
        # from keystoneclient.v3 import client
        # auth = v3.Password(auth_url='https://ned.cloudlab.zhaw.ch:5000/v3', user_id='edmo', password='', project_id='edmo')
        # sess = session.Session(auth=auth)
        # keystone = client.Client(session=sess)
        pass
