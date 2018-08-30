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
import tempfile

# adapters.auth
# esm.auth
auth_role_name = os.environ.get('ET_AAA_ESM_ROLE_NAME', '_member_')
auth_base_url = os.environ.get('ET_AAA_ESM_KEYSTONE_BASE_URL', '')
auth_base_path = os.environ.get('ET_AAA_ESM_KEYSTONE_BASE_PATH', '/v3')
auth_admin_port = os.environ.get('ET_AAA_ESM_KEYSTONE_ADMIN_PORT', 35357)
auth_user_port = os.environ.get('ET_AAA_ESM_KEYSTONE_USER_PORT', 5000)
auth_username = os.environ.get('ET_AAA_ESM_KEYSTONE_USERNAME', '')
auth_passwd = os.environ.get('ET_AAA_ESM_KEYSTONE_PASSWD', '')
auth_tenant = os.environ.get('ET_AAA_ESM_KEYSTONE_TENANT', '')

# adapters.generic
# None

# adapters.log
sen_kafka_ep = os.environ.get('ESM_SENTINEL_KAFKA_ENDPOINT', '')  # localhost:9092
sen_topic = os.environ.get('ESM_SENTINEL_TOPIC', None)  # space
sen_series = os.environ.get('ESM_SENTINEL_SERIES_NAME', None)
sen_agent = os.environ.get('ESM_SENTINEL_AGENT', 'sentinel-internal-log-agent')
sen_key_ser = os.environ.get('ESM_SENTINEL_KAFKA_KEY_SERIALIZER', 'StringSerializer')
sen_val_ser = os.environ.get('ESM_SENTINEL_KAFKA_VALUE_SERIALIZER', 'StringSerializer')

# adapters.log syslog agent
syslog_agent_sentinel_image = os.environ.get('ESM_SENTINEL_SYSLOG_AGENT_IMAGE', 'dizz/sen-syslog-agent:latest')
syslog_agent_sentinel_api_ep = os.environ.get('ESM_SENTINEL_API_ENDPOINT', "")  # http://localhost:9100
syslog_agent_sentinel_available = os.environ.get('SENTINEL_SYSLOG_AVAILABLE', True)
syslog_agent_username = os.environ.get('SENTINEL_SYSLOG_USERNAME', "syslog_agent")
syslog_agent_key = os.environ.get('SENTINEL_SYSLOG_KEY', "")
syslog_agent_bind_address = os.environ.get('SENTINEL_SYSLOG_AGENT_BIND_ADDRESS', "0.0.0.0")
syslog_agent_bind_port = os.environ.get('SENTINEL_SYSLOG_AGENT_BIND_PORT', "4243")

# adapters.measurer
esm_hc_sen_topic = os.environ.get('ESM_SENTINEL_TOPIC', 'user-1-elastest_tss')
esm_hc_sen_series = os.environ.get('ESM_SENTINEL_SERIES_NAME', 'service-health-check'),
esm_hc_sen_max_retries = os.environ.get('ESM_SENTINEL_MAX_RETRIES', '5')
esm_hc_sen_hc_port = os.environ.get('ESM_SENTINEL_HEALTH_CHECK_PORT', '80')
esm_hc_interval = os.environ.get('ESM_SENTINEL_HEALTH_CHECK_INTERVAL', 2)

# adapters.resources
esm_dock_tmp_dir = os.environ.get('ESM_TMP_DIR', tempfile.gettempdir())
esm_dock_inject_logger = os.environ.get('ESM_SENTINEL_INJECT_LOGGER', False)
esm_dock_update_images = os.environ.get('ESM_DOCKER_UPDATE_IMAGES', 'NO')
esm_dock_del_timeout = os.environ.get('ESM_DOCKER_DELETE_TIMEOUT', 20)
esm_epm_api = os.environ.get('ET_EPM_API', 'http://localhost:8180/') + 'v1'

# adapters.sql_store
esm_sql_host = os.environ.get('ESM_SQL_HOST', os.environ.get('ET_EDM_MYSQL_HOST', ''))
esm_sql_port = int(os.environ.get('ESM_SQL_PORT', os.environ.get('ET_EDM_MYSQL_PORT', 3306)))
esm_sql_user = os.environ.get('ESM_SQL_USER', 'root')
esm_sql_password = os.environ.get('ESM_SQL_PASSWORD', '')
esm_sql_database = os.environ.get('ESM_SQL_DBNAME', 'mysql')  # TODO make this something other than mysql!

# adapters.store
esm_mongo_host = os.environ.get('ESM_MONGO_HOST', '')
esm_in_mem = os.environ.get('ESM_IN_MEM', 'YES')

# esm.controllers
esm_measure_insts = os.environ.get('ESM_MEASURE_INSTANCES', 'NO')

# esm
esm_bind_address = os.environ.get('ESM_IP', '0.0.0.0')
esm_bind_port = os.environ.get('ESM_PORT', 8080)
esm_check_ip = os.environ.get('ESM_CHECK_IP', '0.0.0.0')
esm_check_port = os.environ.get('ESM_CHECK_PORT', 5001)


def print_env_vars():
    print('--------------------------------------')
    print('\nActive ESM environment variables:\n ')
    print('--------------------------------------')
    for k, v in os.environ.items():
        print(k + '=' + v)
    print('--------------------------------------')
