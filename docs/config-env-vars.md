**ESM Environment Variables**

Below is the set of environment variables and their defaults that can be set to customise the ESM

**ESM AAA Service Related**

`ET_AAA_ESM_KEYSTONE_BASE_URL` Default is `''`

`ET_AAA_ESM_KEYSTONE_BASE_PATH` Default is `'/v3'`

`ET_AAA_ESM_KEYSTONE_ADMIN_PORT` Default is `35357`

`ET_AAA_ESM_KEYSTONE_USER_PORT` Default is `5001`

`ET_AAA_ESM_KEYSTONE_USERNAME` Default is `''`

`ET_AAA_ESM_KEYSTONE_PASSWD` Default is `''`

`ET_AAA_ESM_KEYSTONE_TENANT` Default is `''`

`ET_AAA_ESM_ROLE_NAME` Default is `'_member_'`

**ESM Endpoint Related**

`ESM_IP` Default is `'0.0.0.0'`

`ESM_PORT` Default is `8080`

**ESM Resource Driver Related**

**Docker**

`ESM_TMP_DIR` Default is the system’s temporary file directory (via tempfile.gettempdir())

`ESM_DOCKER_DELETE_TIMEOUT` Default is `20` seconds

`ESM_DOCKER_UPDATE_IMAGES` Default is `NO`

**EPM**

`ET_EPM_API` Default is `'http://localhost:8180/v1'`

**ESM Storage Driver Related**

**SQL**

`ET_EDM_MYSQL_HOST` or `ESM_SQL_HOST` Default is `''`

`ET_EDM_MYSQL_PORT` or `ESM_SQL_PORT` Default is `3306`

`ESM_SQL_USER` Default is `'root'`

`ESM_SQL_PASSWORD` Default is `''`

`ESM_SQL_DBNAME` Default is `'mysql'`

**MongoDB**

`ESM_MONGO_HOST` Default is `''`

**ESM Health Check Related**

`ESM_CHECK_IP` Default is `'0.0.0.0'`

`ESM_CHECK_PORT` Default is `5000`

**ESM Service Instance Monitoring Related**

`ESM_MEASURE_INSTANCES` Default is `'NO'`

`ESM_SENTINEL_MAX_RETRIES` Default is `'5'` times

`ESM_SENTINEL_HEALTH_CHECK_PORT` Default is `'80'`

`ESM_SENTINEL_HEALTH_CHECK_INTERVAL` Default is `2`

**ESM Sentinel Related**

`ESM_SENTINEL_TOPIC` Default is `None`

`ESM_SENTINEL_AGENT` Default is `None`

`ESM_SENTINEL_KAFKA_ENDPOINT` Default is  `None`

`ESM_SENTINEL_KAFKA_KEY_SERIALIZER` Default is  `None`

`ESM_SENTINEL_KAFKA_VALUE_SERIALIZER` Default is  `None`

`ESM_SENTINEL_SERIES_NAME` Default is `None`

**ESM Test Related**

`DOCKER_TESTS` Default is `'NO’`

`MONGODB_TESTS` Default is `'NO’`

`MYSQL_TESTS` Default is `'NO'`

`HEARTBEAT_TESTS` Default is `'NO'`

`EPM_TESTS` Default is `’NO’`

`SENTINEL_TESTS` Default is `'NO'`