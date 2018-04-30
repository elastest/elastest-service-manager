# User Documentation
## To Run Locally on Docker

```shell
docker run -p 8080:8080 -p 5000:5000 elastest/esm:latest
```

You can now access the ESM service via port `8080` and health checks on port `5000`.

### Viewing the API via Swagger

Navigate to the following URL in your browser

```
http://localhost:8080/ui/
```

The OSBA Swagger definition can be accessed here:

```
http://localhost:8080/swagger.json
```

## Deploy on Docker-Compose

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

## Using the ESM API
Once you have an ESM instance running you can interact with it using `curl`, [Postman](https://www.getpostman.com) or generate a client from the swagger specification.

To use the API please see the [open service broker API specification](https://www.openservicebrokerapi.org/) or use the UI version from within your browser.

### Register a Service

```shell
curl -X PUT \
  http://localhost:8080/v2/et/catalog \
  -H 'accept: application/json' \
  -H 'content-type: application/json' \
  -H 'x-broker-api-version: 2.12' \
  -d '{
  "description": "this is a test service",
  "id": "testsvc",
  "name": "test_svc",
  "bindable": false,
  "plan_updateable": false,
  "plans": [
    {
      "bindable": false,
      "description": "plan for testing",
      "free": true,
      "id": "testplan",
      "name": "testing plan",
      "metadata": {
        "costs": {
          "name": "On Demand 5 + Charges",
          "type": "ONDEMAND",
          "fix_cost": {
            "deployment": 5
          },
          "var_rate": {
            "disk": 1,
            "memory": 10,
            "cpus": 50
          },
          "components": {
          },
          "description": "On Demand 5 per deployment, 50 per core, 10 per GB ram and 1 per GB disk"
        },
        "bullets": "basic plan"
      }
    }
  ],
  "requires": [],
  "tags": [
    "test",
    "tester"
  ]
}
'
```

### Get the Catalog

```shell
curl -v -X GET http://localhost:8080/v2/catalog -H 'X_Broker_Api_Version: 2.12'
```
<details>
  <summary>Shell Output</summary>

  ```shell
  Note: Unnecessary use of -X or --request, GET is already inferred.
  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to 127.0.0.1 (127.0.0.1) port 8080 (#0)
  > GET /v2/catalog HTTP/1.1
  > Host: 127.0.0.1:8080
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
</details>

### Register a Manifest for a Service's Plan

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
    "manifest_content": "version: '2'\n\nservices:\n  spark-master:\n    image: elastest/ebs-spark-base:0.5.0\n    container_name: spark-master\n    ports:\n      - \"8080:8080\"\n    volumes:\n      - ./spark/alluxio_conf:/opt/alluxio/conf\n      - ./spark/spark_conf:/opt/spark/conf\n      - ./spark/hadoop_conf:/usr/local/hadoop/etc/hadoop\n    command: [\"/usr/bin/supervisord\", \"--configuration=/opt/conf/master.conf\"]\n    hostname: spark-master\n    networks:\n      - elastest\n\n  spark-worker:\n    image: elastest/ebs-spark-base:0.5.0\n    depends_on:\n      - spark-master\n    ports:\n      - \"8081\"\n    volumes:\n      - ./spark/alluxio_conf:/opt/alluxio/conf\n      - ./spark/spark_conf:/opt/spark/conf\n      - ./spark/hadoop_conf:/usr/local/hadoop/etc/hadoop\n    command: [\"/usr/bin/supervisord\", \"--configuration=/opt/conf/slave.conf\"]\n    hostname: spark-worker\n    networks:\n      - elastest\n\nnetworks:\n  elastest:\n    external: true\n",
    "manifest_type": "dummy",
    "plan_id": "testplan",
    "service_id": "testsvc"
  }'
```

### Get the Manifests

```shell
curl -v GET http://localhost:8080/v2/et/manifest -H 'X_Broker_Api_Version: 2.12'
```

<details>
  <summary>Shell Output</summary>

  ```shell
  * Rebuilt URL to: GET/
  * Could not resolve host: GET
  * Closing connection 0
  curl: (6) Could not resolve host: GET
  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to 127.0.0.1 (127.0.0.1) port 8080 (#1)
  > GET /v2/et/manifest HTTP/1.1
  > Host: 127.0.0.1:8080
  > User-Agent: curl/7.54.0
  > Accept: */*
  > X_Broker_Api_Version: 2.12
  >
  < HTTP/1.1 200 OK
  < Content-Type: application/json
  < Content-Length: 179
  < Server: TornadoServer/4.5.2
  <
  [
    {
      "id": "test_manifest",
      "manifest_content": "some-content",
      "manifest_type": "dummy",
      "plan_id": "plan-id-for-free",
      "service_id": "a_service_type"
    }
  ]
  * Connection #1 to host 127.0.0.1 left intact
  ```
</details>


### Provision (create) a service instance

```shell
curl -v -d @payload.json -X PUT -H "X-Broker-API-Version: 2.12" -H "Content-Type: application/json" http://localhost:8080/v2/service_instances/test_service_instance?accept_incomplete=false
```

where `payload.json` is:

```json
{
  "organization_guid": "org",
  "plan_id": "testplan",
  "service_id": "testsvc",
  "space_guid": "space"
}
```

<details>
  <summary>Shell Output</summary>

  ```shell
  *   Trying ::1...
  * TCP_NODELAY set
  * Connection failed
  * connect to ::1 port 8080 failed: Connection refused
  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to localhost (127.0.0.1) port 8080 (#0)
  > PUT /v2/service_instances/123-123-123?accept_incomplete=true HTTP/1.1
  > Host: localhost:8080
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
</details>



### Get the Service Instances

```shell
curl -v GET http://localhost:8080/v2/et/service_instances -H 'X_Broker_Api_Version: 2.12'
```
<details>
  <summary>Shell Output</summary>

  ```shell
  * Rebuilt URL to: GET/
  * Could not resolve host: GET
  * Closing connection 0
  curl: (6) Could not resolve host: GET
  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to 127.0.0.1 (127.0.0.1) port 8080 (#1)
  > GET /v2/et/service_instances HTTP/1.1
  > Host: 127.0.0.1:8080
  > User-Agent: curl/7.54.0
  > Accept: */*
  > X_Broker_Api_Version: 2.12
  >
  < HTTP/1.1 200 OK
  < Content-Type: application/json
  < Content-Length: 1597
  < Server: TornadoServer/4.5.2
  <
  [
    {
      "context": {
        "id": "123-123-123",
        "manifest_id": "test_manifest",
        "spark-master_8080/tcp/HostIp": "0.0.0.0",
        "spark-master_8080/tcp/HostPort": "8080",
        "spark-master_cmd": "/usr/bin/supervisord --configuration=/opt/conf/master.conf",
        "spark-master_image_id": "sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb",
        "spark-master_image_name": "elastest/ebs-spark-base:0.5.0",
        "spark-master_state": "Up",
        "testid123_spark-worker_1_8080/tcp": null,
        "testid123_spark-worker_1_8081/tcp/HostIp": "0.0.0.0",
        "testid123_spark-worker_1_8081/tcp/HostPort": "32784",
        "testid123_spark-worker_1_cmd": "/usr/bin/supervisord --configuration=/opt/conf/slave.conf",
        "testid123_spark-worker_1_image_id": "sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb",
        "testid123_spark-worker_1_image_name": "elastest/ebs-spark-base:0.5.0",
        "testid123_spark-worker_1_state": "Up"
      },
      "service_type": {
        "bindable": false,
        "description": "this is a test service",
        "id": "a_service_type",
        "name": "test_svc",
        "plan_updateable": false,
        "plans": [
          {
            "bindable": false,
            "description": "plan for testing",
            "free": true,
            "id": "plan-id-for-free",
            "name": "testing plan"
          }
        ],
        "requires": [],
        "tags": [
          "test",
          "tester"
        ]
      },
      "state": {
        "description": "The service instance is being created.",
        "state": "in progress"
      }
    }
  ]
  * Connection #1 to host 127.0.0.1 left intact
  ```
</details>


### Get the Service Instance Information

```shell
curl -v -X GET http://localhost:8080/v2/et/service_instances/test_service_instance -H 'X_Broker_Api_Version: 2.12'
```

<details>
  <summary>Shell Output</summary>

  ```shell
  * Rebuilt URL to: GET/
  * Could not resolve host: GET
  * Closing connection 0
  curl: (6) Could not resolve host: GET
  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to 127.0.0.1 (127.0.0.1) port 8080 (#1)
  > GET /v2/et/service_instances/123-123-123 HTTP/1.1
  > Host: 127.0.0.1:8080
  > User-Agent: curl/7.54.0
  > Accept: */*
  > X_Broker_Api_Version: 2.12
  >
  < HTTP/1.1 200 OK
  < Content-Type: application/json
  < Content-Length: 1505
  < Server: TornadoServer/4.5.2
  <
  {
    "context": {
      "id": "123-123-123",
      "manifest_id": "test_manifest",
      "spark-master_8080/tcp/HostIp": "0.0.0.0",
      "spark-master_8080/tcp/HostPort": "8080",
      "spark-master_cmd": "/usr/bin/supervisord --configuration=/opt/conf/master.conf",
      "spark-master_image_id": "sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb",
      "spark-master_image_name": "elastest/ebs-spark-base:0.5.0",
      "spark-master_state": "Up",
      "testid123_spark-worker_1_8080/tcp": null,
      "testid123_spark-worker_1_8081/tcp/HostIp": "0.0.0.0",
      "testid123_spark-worker_1_8081/tcp/HostPort": "32784",
      "testid123_spark-worker_1_cmd": "/usr/bin/supervisord --configuration=/opt/conf/slave.conf",
      "testid123_spark-worker_1_image_id": "sha256:138a91572bd6bdce7d7b49a44b91a4caf4abdf1a75f105991e18be971353d5cb",
      "testid123_spark-worker_1_image_name": "elastest/ebs-spark-base:0.5.0",
      "testid123_spark-worker_1_state": "Up"
    },
    "service_type": {
      "bindable": false,
      "description": "this is a test service",
      "id": "a_service_type",
      "name": "test_svc",
      "plan_updateable": false,
      "plans": [
        {
          "bindable": false,
          "description": "plan for testing",
          "free": true,
          "id": "plan-id-for-free",
          "name": "testing plan"
        }
      ],
      "requires": [],
      "tags": [
        "test",
        "tester"
      ]
    },
    "state": {
      "description": "The service instance is being created.",
      "state": "in progress"
    }
  }
  * Connection #1 to host 127.0.0.1 left intact
  ```
</details>


### Deprovision (delete) a service instance

```shell
curl -v -X DELETE -H "X-Broker-API-Version: 2.12" -H "Content-Type: application/json" http://localhost:8080/v2/service_instances/test_service_instance?service_id=test&plan_id=testplan&accept_incomplete=false
```
<details>
  <summary>Shell Output</summary>

  ```shell
  * Trying ::1...
  * TCP_NODELAY set
  * Connection failed
  * connect to ::1 port 8080 failed: Connection refused
  *   Trying 127.0.0.1...
  * TCP_NODELAY set
  * Connected to localhost (127.0.0.1) port 8080 (#0)
  > DELETE /v2/service_instances/123-123-123?service_id=a_service_type&plan_id=plan-id-for-free HTTP/1.1
  > Host: localhost:8080
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
</details>




### Bind and Unbind

Currently not supported.

## Using the Health API

There are two endpoints that are available to check the health of the ESM

* `http://$ESM_HOST:$ESM_CHECK_PORT/health`: this current performs a very simple check. It will be extended to provide a light weight check on the ESM's Store and Resource Managers.
* `http://$ESM_HOST:$ESM_CHECK_PORT/environment`: returns environment settings which the ESM is loaded with.

Both endpoints only support GET. Below is the output of issuing the HTTP GET to each endpoint.

### /health Endpoint

```shell
$ curl http://localhost:5000/health
{"hostname": "swizz", "status": "success", "timestamp": 1501062260.8501298, "results": [{"checker": "health_check", "output": "addition works", "passed": true, "timestamp": 1501062260.8501172, "expires": 1501062287.8501172}]}
```

### /environment Endpoint

```
curl http://localhost:5000/environment
```
<details>
  <summary>Shell Output</summary>

  ```shell
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
</details>

## Configuring ESM

Please see the [set of configuration environment variables here](./config-env-vars.md)

## Authentication

The ESM supports a simple mode where no authentication is provided. If authentication is required then the use of [OpenStack Keystone](https://github.com/openstack/keystone) is supported. To enable this support, simply set the following environment variables:

* `ET_AAA_ESM_KEYSTONE_BASE_URL`: **Required**. This is the base URL of where the keystone service is running e.g. `http://localhost'. 
* `ET_AAA_ESM_KEYSTONE_USERNAME`: **Required**. This is the name of a user that has permissions to verify tokens created by the keystone service.
* `ET_AAA_ESM_KEYSTONE_PASSWD`: **Required**. This is the password of the corresponding username.
* `ET_AAA_ESM_KEYSTONE_TENANT`: **Required**. This is the tenant or project of the corresponding username.
* `ET_AAA_ESM_KEYSTONE_ADMIN_PORT`: This is the port number where the admin keystone service runs. The default is `35357`.
* `ET_AAA_ESM_KEYSTONE_USER_PORT`: This is the port number where the normal keystone service runs (used by regular users). The default is `5000`.

### Running OpenStack Keystone

If you want to run your own instance of keystone on docker [see the following repository](https://github.com/dizz/dock-os-keystone) for details.