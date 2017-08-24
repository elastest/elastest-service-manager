[![][ElasTest Logo]][ElasTest]

Copyright © 2017-2019 Zuercher Hochschule fuer Angewandte Wissenschaften. Licensed under [Apache 2.0 License].

# elastest-service-manager (esm)

## Features

The service manager is based around the idea of delivering service instances to end-user consumers. 
For this the service provider needs an efficient and easy way to present their software to the service manager.
To do this the service manager supports deployment using docker-compose descriptions and will soon support 
kubernetes-based descriptions.
In order to use the facility of the service manager, its API is used. The API is based upon the latest (2.12) version of 
the Open Service Broker API. To this there are some specific ElasTest extensions added. 

## API Features

The following features are currently supported:

 * OSBA: list the contents of the service catalog.
 * OSBA: create a service instance.
 * OSBA: delete a service instance.
 * ElasTest Extension: get details on a service instance.
 * ElasTest Extension: register a service in the service catalog.
 * ElasTest Extension: register a service manifest (docker-compose, docker-swarm) associated with a service description.

### API Features to be Implemented

The following features will be supported in upcoming releases:

 * OSBA: binding a service instance
 * OSBA: binding a service instance

## How To Run
### To Run Locally on Docker

```shell
docker run -p 8080:8080 -p 5000:5000 elastest/elastest-service-manager
```

You can now access the ESM service via port `8080` and health checks on port `5000`.

#### Viewing the API via Swagger

Navigate to the following URL in your browser

```
http://localhost:8080/v2/ui/
```

The OSBA Swagger definition can be accessed here:

```
http://localhost:8080/v2/swagger.json
```

### Deploy on Docker-Compose

There is are two docker compose files:
 * `./deploy/docker-compose.yml`: this will create the ESM along with its DB and a full ELK stack to monitor the ESM.
 * `./deploy/docker-compose-no-mon.yml` this will create the ESM along with only its DB.

 You can use this to bring up the ESM with a DB backend.

```shell
docker-compose up
```

**Notes**:

* By default this compose file will create a persistent mongodb service. If you do not want this then remove the `MONGO_DB` env. var. from the compose file. 
* By default the port that the ESM will listen to is `8080`. If  you want it to listen under a different port then adjust the `ESM_PORT` env. var. in the compose file.

### Deploy on OpenShift

This description will follow.

<!--There are deployment manifests within `./deploy` that will deploy a service broker to OpenShift. There are two main modifications that you will have to do:

1. Change the route `./deploy/sv_route.yaml`. See line 11.
2. Change the configuration of the service broker. Configuration is done by modifying `./deploy/sb_dc.yaml` under the `env` stanza, lines 31-38. 
3. Deploy: `oc create -f ./deploy`.
4. Build: `oc start-build svcbroker`.
5. Destroy: `oc delete -f ./deploy`. -->

### Deploy on K8s

This description will follow.

## Basic Usage

### Using the ESM API

To use the API please see the [open service broker API specification](https://www.openservicebrokerapi.org/) or use the UI version from within your browser.

#### Register a Service

```shell
curl -X PUT \
  http://localhost:8080/v2/et/catalog \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-broker-api-version: 2.12' \
  -d '{
  "description": "this is a test service",
  "id": "test",
  "name": "test_svc",
  "bindable": false,
  "plan_updateable": false,
  "plans": [
    {
      "bindable": false,
      "description": "plan for testing",
      "free": true,
      "id": "testplan",
      "name": "testing plan"
    }
  ],
  "requires": [],
  "tags": [
    "test",
    "tester"
  ]
}
```

#### Register a Manifest for a Service's Plan

```shell
  curl -X PUT \
  http://localhost:8080/v2/et/manifest/test_manifest \
  -H 'accept: application/json' \
  -H 'cache-control: no-cache' \
  -H 'content-type: application/json' \
  -H 'postman-token: af2a8114-34cb-cf54-a863-4ad4672ad8c1' \
  -H 'x-broker-api-version: 2.12' \
  -d '{
  "id": "test-mani",
  "manifest_content": "version: '\''2'\''</br></br>services:</br>  spark-master:</br>    image: elastest/ebs-spark-base:0.5.0</br>    container_name: spark-master</br>    ports:</br>      - \"8080:8080\"</br>    volumes:</br>      - ./spark/alluxio_conf:/opt/alluxio/conf</br>      - ./spark/spark_conf:/opt/spark/conf</br>      - ./spark/hadoop_conf:/usr/local/hadoop/etc/hadoop</br>    command: [\"/usr/bin/supervisord\", \"--configuration=/opt/conf/master.conf\"]</br>    hostname: spark-master</br>    networks:</br>      - elastest</br></br>  spark-worker:</br>    image: elastest/ebs-spark-base:0.5.0</br>    depends_on:</br>      - spark-master</br>    ports:</br>      - \"8081\"</br>    volumes:</br>      - ./spark/alluxio_conf:/opt/alluxio/conf</br>      - ./spark/spark_conf:/opt/spark/conf</br>      - ./spark/hadoop_conf:/usr/local/hadoop/etc/hadoop</br>    command: [\"/usr/bin/supervisord\", \"--configuration=/opt/conf/slave.conf\"]</br>    hostname: spark-worker</br>    networks:</br>      - elastest</br></br>networks:</br>  elastest:</br>    external: true</br>",
  "manifest_type": "dummy",
  "plan_id": "testplan",
  "service_id": "test-svc"
}
```

#### Get the Catalog

```shell
curl -v -X GET http://127.0.0.1:9999/v2/catalog -H 'X_Broker_Api_Version: 2.12'
Note: Unnecessary use of -X or --request, GET is already inferred.
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to 127.0.0.1 (127.0.0.1) port 9999 (#0)
> GET /v2/catalog HTTP/1.1
> Host: 127.0.0.1:9999
> User-Agent: curl/7.51.0
> Accept: */*
> X_Broker_Api_Version: 2.11
>
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Content-Type: application/json
< Content-Length: 449
< Server: Werkzeug/0.11.15 Python/3.6.0
< Date: Thu, 09 Mar 2017 16:03:43 GMT
<
{
  "services": [
    {
      "bindable": false,
      "description": "Monitoring service",
      "id": "a_service_type",
      "name": "a service name",
      "plan_updateable": false,
      "plans": [
        {
          "description": "This is a best effort plan. No SLA, QoS, QoE or anything like that is guaranteed",
          "id": "best_effort",
          "name": "Best effort plan"
        }
      ],
      "tags": []
    }
  ]
}
```

#### Provision (create) a service instance

```shell
curl -v -d @payload.json -X PUT -H "X-Broker-API-Version: 2.12" -H "Content-Type: application/json" http://localhost:9999/v2/service_instances/123-123-123\?accept_incomplete\=true
```

where `payload.json` is:

```json
{
  "organization_guid": "my-org-id-very-rich-company",
  "plan_id":           "plan-id-for-free",
  "service_id":        "a_service_type",
  "space_guid":        "space-guid-here",
  "parameters":        {
    "parameter1": 1,
    "parameter2": "value"
  }
}
```

`curl` will output

```shell
*   Trying ::1...
* TCP_NODELAY set
* Connection failed
* connect to ::1 port 9999 failed: Connection refused
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to localhost (127.0.0.1) port 9999 (#0)
> PUT /v2/service_instances/123-123-123?accept_incomplete=true HTTP/1.1
> Host: localhost:9999
> User-Agent: curl/7.51.0
> Accept: */*
> X-Broker-API-Version: 2.12
> Content-Type: application/json
> Content-Length: 272
>
* upload completely sent off: 272 out of 272 bytes
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Content-Type: application/json
< Content-Length: 119
< Server: Werkzeug/0.11.15 Python/3.6.0
< Date: Thu, 09 Mar 2017 16:12:47 GMT
<
{
  "dashboard_url": "http://mon.sm.192.168.64.4.xip.io/mon/somon2c1e6fa57ac0154e",
  "operation": "provisioning..."
}
```

#### Deprovision (delete) a service instance

```shell
curl -v -X DELETE -H "X-Broker-API-Version: 2.12" -H "Content-Type: application/json" http://localhost:9999/v2/service_instances/123-123-123\?service_id\="a_service_type"\&plan_id\="plan-id-for-free"
*   Trying ::1...
* TCP_NODELAY set
* Connection failed
* connect to ::1 port 9999 failed: Connection refused
*   Trying 127.0.0.1...
* TCP_NODELAY set
* Connected to localhost (127.0.0.1) port 9999 (#0)
> DELETE /v2/service_instances/123-123-123?service_id=a_service_type&plan_id=plan-id-for-free HTTP/1.1
> Host: localhost:9999
> User-Agent: curl/7.51.0
> Accept: */*
> X-Broker-API-Version: 2.12
> Content-Type: application/json
>
* HTTP 1.0, assume close after body
< HTTP/1.0 200 OK
< Content-Type: application/json
< Content-Length: 5
< Server: Werkzeug/0.11.15 Python/3.6.0
< Date: Fri, 10 Mar 2017 16:17:36 GMT
<
null
```



#### Bind and Unbind

Currently not supported.

### Using the Health API

There are two endpoints that are available to check the health of the ESM

* `http://$ESM_HOST:$ESM_CHECK_PORT/health`: this current performs a very simple check. It will be extended to provide a light weight check on the ESM's Store and Resource Managers.
* `http://$ESM_HOST:$ESM_CHECK_PORT/environment`: returns environment settings which the ESM is loaded with.

Both endpoints only support GET. Below is the output of issuing the HTTP GET to each endpoint.

#### /health Endpoint

```shell
$ curl http://localhost:5000/healthcheck
{"hostname": "swizz", "status": "success", "timestamp": 1501062260.8501298, "results": [{"checker": "health_check", "output": "addition works", "passed": true, "timestamp": 1501062260.8501172, "expires": 1501062287.8501172}]}
```

#### /environment Endpoint

```
curl http://localhost:5000/environment
{
	"os": {
		"platform": "darwin",
		"name": "posix",
		"uname": ["Darwin", "swizz", "16.7.0", "Darwin Kernel Version 16.7.0: Thu Jun 15 17:36:27 PDT 2017; root:xnu-3789.70.16~2/RELEASE_X86_64", "x86_64"]
	},
	"python": {
		"version": "3.6.2 (default, Jul 17 2017, 16:44:45) \n[GCC 4.2.1 Compatible Apple LLVM 8.1.0 (clang-802.0.42)]",
		"executable": "/Users/andy/Source/ElasTest/elastest-service-manager/.env/bin/python",
		"pythonpath": ["/Users/andy/Source/ElasTest/elastest-service-manager", "/Users/andy/Source/ElasTest/elastest-service-manager/.env/lib/python36.zip", "/Users/andy/Source/ElasTest/elastest-service-manager/.env/lib/python3.6", "/Users/andy/Source/ElasTest/elastest-service-manager/.env/lib/python3.6/lib-dynload", "/usr/local/Cellar/python3/3.6.2/Frameworks/Python.framework/Versions/3.6/lib/python3.6", "/Users/andy/Source/ElasTest/elastest-service-manager/.env/lib/python3.6/site-packages"],
		"version_info": {
			"major": 3,
			"minor": 6,
			"micro": 2,
			"releaselevel": "final",
			"serial": 0
		},
		"packages": {
			"wrapt": "1.10.10",
			"wheel": "0.29.0",
			"Werkzeug": "0.12.2",
			"websocket-client": "0.44.0",
			"virtualenv": "15.1.0",
			"urllib3": "1.21.1",
			"tzlocal": "1.4",
			"typed-ast": "1.0.4",
			"tox": "2.7.0",
			"tornado": "4.5.1",
			"texttable": "0.8.8",
			"swagger-spec-validator": "2.1.0",
			"strict-rfc3339": "0.7",
			"six": "1.10.0",
			"setuptools": "36.2.0",
			"rsa": "3.4.2",
			"requests": "2.18.1",
			"requests-oauthlib": "0.8.0",
			"randomize": "0.14",
			"PyYAML": "3.12",
			"pytz": "2017.2",
			"python-dateutil": "2.6.0",
			"pymongo": "3.4.0",
			"pylint": "1.7.2",
			"pykube": "0.15.0",
			"pyasn1": "0.2.3",
			"pyasn1-modules": "0.0.9",
			"py": "1.4.34",
			"pluggy": "0.4.0",
			"pip": "9.0.1",
			"oauthlib": "2.0.2",
			"oauth2client": "4.1.2",
			"nose": "1.3.7",
			"mypy": "0.521",
			"mccabe": "0.6.1",
			"MarkupSafe": "1.0",
			"lazy-object-proxy": "1.3.1",
			"jsonschema": "2.6.0",
			"Jinja2": "2.9.6",
			"itsdangerous": "0.24",
			"isort": "4.2.15",
			"idna": "2.5",
			"httplib2": "0.10.3",
			"healthcheck": "1.3.2",
			"Flask": "0.12.2",
			"Flask-Testing": "0.6.1",
			"docopt": "0.6.2",
			"dockerpty": "0.4.1",
			"docker": "2.4.2",
			"docker-pycreds": "0.2.1",
			"docker-compose": "1.14.0",
			"daiquiri": "1.2.1",
			"coverage": "4.4.1",
			"connexion": "1.0.129",
			"colorama": "0.3.9",
			"clickclick": "1.2.2",
			"click": "6.7",
			"chardet": "3.0.4",
			"certifi": "2017.4.17",
			"cached-property": "1.3.0",
			"astroid": "1.5.3"
		}
	},
	"config": {
		"DEBUG": false,
		"TESTING": false,
		"PROPAGATE_EXCEPTIONS": null,
		"PRESERVE_CONTEXT_ON_EXCEPTION": null,
		"SECRET_KEY": "********",
		"USE_X_SENDFILE": false,
		"LOGGER_NAME": "check_api",
		"LOGGER_HANDLER_POLICY": "always",
		"SERVER_NAME": null,
		"APPLICATION_ROOT": null,
		"SESSION_COOKIE_NAME": "session",
		"SESSION_COOKIE_DOMAIN": null,
		"SESSION_COOKIE_PATH": null,
		"SESSION_COOKIE_HTTPONLY": true,
		"SESSION_COOKIE_SECURE": false,
		"SESSION_REFRESH_EACH_REQUEST": true,
		"MAX_CONTENT_LENGTH": null,
		"TRAP_BAD_REQUEST_ERRORS": false,
		"TRAP_HTTP_EXCEPTIONS": false,
		"EXPLAIN_TEMPLATE_LOADING": false,
		"PREFERRED_URL_SCHEME": "http",
		"JSON_AS_ASCII": true,
		"JSON_SORT_KEYS": "********",
		"JSONIFY_PRETTYPRINT_REGULAR": true,
		"JSONIFY_MIMETYPE": "application/json",
		"TEMPLATES_AUTO_RELOAD": null
	},
	"process": {
		"argv": ["./runesm.py"],
		"cwd": "/Users/andy/Source/ElasTest/elastest-service-manager",
		"user": "andy",
		"pid": 58944,
		"environ": {
			"TERM_SESSION_ID": "w0t1p0:F65D8DE9-CDD3-4243-93A2-54A3620AE40C",
			"SSH_AUTH_SOCK": "/private/tmp/com.apple.launchd.gofU2TOVaJ/Listeners",
			"Apple_PubSub_Socket_Render": "/private/tmp/com.apple.launchd.TFApj7GXcU/Render",
			"COLORFGBG": "15;0",
			"ITERM_PROFILE": "Default",
			"XPC_FLAGS": "0x0",
			"PWD": "/Users/andy/Source/ElasTest/elastest-service-manager",
			"SHELL": "/usr/local/bin/zsh",
			"LC_CTYPE": "UTF-8",
			"TERM_PROGRAM_VERSION": "3.1.beta.5",
			"TERM_PROGRAM": "iTerm.app",
			"PATH": "/Users/andy/Source/ElasTest/elastest-service-manager/.env/bin:/usr/local/heroku/bin:/Users/andy/Source/go/bin:/bin:/sbin:/Applications/Vagrant/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin:/usr/X11/bin:/Users/andy/bin:/usr/texbin:/Users/andy/bin/arcanist/bin",
			"COLORTERM": "truecolor",
			"TERM": "xterm-256color",
			"HOME": "/Users/andy",
			"TMPDIR": "/var/folders/mv/psmjhjw94f15167vzcwhdygw0000gp/T/",
			"USER": "andy",
			"XPC_SERVICE_NAME": "0",
			"LOGNAME": "andy",
			"__CF_USER_TEXT_ENCODING": "0x1F6:0x0:0x2",
			"ITERM_SESSION_ID": "w0t1p0:F65D8DE9-CDD3-4243-93A2-54A3620AE40C",
			"SHLVL": "1",
			"PAGER": "less",
			"LESS": "-R",
			"LSCOLORS": "Gxfxcxdxbxegedabagacad",
			"VAGRANT": "/Applications/Vagrant/bin",
			"EDITOR": "subl -w",
			"GOPATH": "/Users/andy/Source/go",
			"GOVERSION": "1.8.3",
			"GOROOT": "/usr/local/Cellar/go/1.8.3/libexec",
			"VIRTUAL_ENV": "/Users/andy/Source/ElasTest/elastest-service-manager/.env",
			"ESM_MONGO_HOST": "localhost",
			"_": "/Users/andy/Source/ElasTest/elastest-service-manager/.env/bin/python"
		}
	},
	"application": {
		"maintainer": "ElasTest",
		"git_repo": "https://github.com/elastest/elastest-service-manager"
	}
}
```



## Development Documentation

### Service Manager API
This service broker was in part generated by the [swagger-codegen](https://github.com/swagger-api/swagger-codegen) project. By using the [OpenAPI-Spec](https://github.com/swagger-api/swagger-core/wiki) from a remote server, you can easily generate a server stub. Using the swagger specification for this broker, you can also generate a client to interact with the broker, should `curl` not be your preference. The implementation uses the [Connexion](https://github.com/zalando/connexion) library on top of Flask and requires Python 3.6. To use Python 3.5 you will need the `typing` module dependency, but this is included in the `requirements.txt` file. Python 2.x is not supported.

See `./gen_api_skels.sh` on how the command line is to generate the code.

The ESM uses the [Connexion](https://github.com/zalando/connexion) library on top of Flask.

To run the ESM, please execute the following from the root directory:

```
virtualenv .env
source .env/bin/activate
pip3 install -r requirements.txt
python3 ./runesm.py
```

If you want to view the Swagger UI you can simply navigate to this URL in your browser:
```
http://localhost:8080/ui/
```

To retrieve the swagger specification of the running ESM simply use `curl` or `wget` against this URL
```
http://localhost:8080/swagger.json
```

To launch the integration tests, use tox:
```
pip install tox
tox
```
### Running Tests

```shell
sudo pip install tox
tox
```

Ensure that you run from a virtual environments:

```shell
virtualenv .env
source .env/bin/activate
```

To launch the tests, use tox. Ensure the test requirements are installed:

`pip install -r test-requirements.txt`

From the root of the project you can run all tests with:

```
sudo pip install tox
tox
```

By default, the mongodb backend is enabled in tox. If you want to change this or if the Docker tests are run edit the variables `MONGODB_TESTS` and/or `DOCKER_TESTS` in `tox.ini`.

If you don't want to run and use `nosetests` you can easily do so. To enable/disable the Mongo or Docker tests simply set the shell variables of `MONGODB_TESTS` and/or `DOCKER_TESTS` to `YES` or `NO`.

To interact with the API after running `runsm.py`, you can use the [Postman](https://www.getpostman.com) collection that's under `tests/postman`.

You can see the [current test coverage here](https://codecov.io/gh/elastest/elastest-service-manager).


### Extending

#### Data Store

Subclass `adapters.datastore.Store` and implement for you persistence system.

Currently supported:

* `adapters.datastore.InMemoryStore`: this is a datastore driver that holds all ESM state in memory. To be used for testing only as restarting the ESM process will destroy all recorded information.


* `adapters.datastore.MongoDB`: this is a datastore driver that persists all ESM state into mongodb. Data is kept across reboots of the ESM process.

#### Resource Manager

Subclass `adapters.resources.Backend` and implement for you persistence system. You will then have to register your Backend driver with the `adapters.resources.ResourceManager` class.

Currently supported:

* `adapters.resources.DummyBackend`: This is a NoOp driver used for speedy testing.


* `adapters.resources.DockerBackend`: Uses a docker-compose file to deploy the service software. This can point not only to a local docker deployment (not distributed), but also to a docker swarm.

### Building with Docker

There is a docker build file `./Dockerfile` in the root of this project. You can use this to create a docker image that can then be ran upon your local docker environment.

#### To Build Locally

```shell
docker build -t elastest/elastest-service-manager:latest ./
```

### Running the ESM Outside of a Virtualisation Technology

Ensure you have all dependencies required: `pip3 install -r requirements.txt`

Configure the following OS environment variables:

* `ESM_PORT`: this is the port under which the service broker runs. By default it runs on `8080`.
* `ESM_CHECK_PORT`: this is the port where health checks are served. By default it runs on `5000`.
* `ESM_MONGO_HOST`: this is the host where a mongodb service is running. It is used to persist ESM state. If it's not set then an in-memory store is used.

Example config and run:

```shell
$ export ESM_PORT=9999
$ export ESM_CHECK_PORT=8888
$ export ESM_MONGO_HOST=localhost
$ python ./runesm.py
2017-07-26 11:37:22,918 [58778] INFO     adapters.datasource: Using the MongoDBStore.
2017-07-26 11:37:22,918 [58778] INFO     adapters.datasource: MongoDBStore is persistent.
2017-07-26 11:37:23,382 [58778] INFO     adapters.resources: Adding docker-compose alias to DockerBackend
2017-07-26 11:37:23,382 [58778] INFO     adapters.resources: Adding k8s alias to KubernetesBackend
2017-07-26 11:37:23,389 [58778] INFO     __main__: OSBA API and ElasTest extensions API created.
2017-07-26 11:37:23,390 [58778] INFO     __main__: ESM available at http://0.0.0.0:9999
2017-07-26 11:37:23,390 [58778] INFO     __main__: ESM Health available at http://0.0.0.0:8888
2017-07-26 11:37:23,390 [58778] INFO     __main__: Press CTRL+C to quit.
```

The service manager endpoint should only be the scheme (http or https) and the fully qualified host name, optionally including the port number if it differs from the standard port 80 or 443.


### Notes

To build the swagger-codegen [tool yourself](https://github.com/swagger-api/swagger-codegen/tree/master#building)

``` sh
# server files
# assumes a brew installation of swagger code gen
SWAGGER_CODE_GEN="/usr/local/bin/swagger-codegen"
$SWAGGER_CODE_GEN generate -i  ./api.yaml -l python-flask -o ./ -DpackageName=esm --import-mappings object=#

# client files
$SWAGGER_CODE_GEN generate -i  ./apidef/swagger/open_service_broker_api.yaml -l python -o ./client -DpackageName=esm-client
```

## Service Providers Usage

If you wish to use the ESM to deliver service instances of your software you need the following:

* All software components packaged as services within docker images.
* Those images should be available in an image registry that is accessible by the ESM
* A description of how those docker images are composed. Currently only the docker-compose/docker-swarm format is supported. Kubernetes will be supported through the use of Helm templates.

Once these items are available then the service provider simply needs to:

* Register the service with the ESM's catalog
* Register the service manifest with the ESM

# Source

Source code for other ElasTest projects can be found in the [GitHub ElasTest Group].

# Support
If you need help and support with the ESM, please refer to the ElasTest [Bugtracker]. 
Here you can find the help you need.

# News
Follow us on Twitter @[ElasTest Twitter].

# Contribution Policy
You can contribute to the ElasTest community through bug-reports, bug-fixes,
new code or new documentation. For contributing to the ElasTest community,
you can use the issue support of GitHub providing full information about your
contribution and its value. In your contributions, you must comply with the
following guidelines

* You must specify the specific contents of your contribution either through a
  detailed bug description, through a pull-request or through a patch.
* You must specify the licensing restrictions of the code you contribute.
* For newly created code to be incorporated in the ElasTest code-base, you
  must accept ElasTest to own the code copyright, so that its open source
  nature is guaranteed.
* You must justify appropriately the need and value of your contribution. The
  ElasTest project has no obligations in relation to accepting contributions
  from third parties.
* The ElasTest project leaders have the right of asking for further
  explanations, tests or validations of any code contributed to the community
  before it being incorporated into the ElasTest code-base. You must be ready
  to addressing all these kind of concerns before having your code approved.

# Licensing and distribution
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


[Apache 2.0 License]: http://www.apache.org/licenses/LICENSE-2.0
[ElasTest]: http://elastest.io/
[ElasTest Logo]: http://elastest.io/images/logos_elastest/elastest-logo-gray-small.png
[ElasTest Twitter]: https://twitter.com/elastestio
[GitHub ElasTest Group]: https://github.com/elastest
[Bugtracker]: https://github.com/elastest/bugtracker
