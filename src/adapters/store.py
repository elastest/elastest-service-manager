# -*- coding: utf-8 -*-

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

import config
import pymysql
import time
from typing import List


if config.esm_mongo_host != '':
    from pymongo import MongoClient

from esm.models import LastOperation
from esm.models import Manifest
from esm.models import ServiceInstance
from esm.models import ServiceType

from adapters.sql_store import Helper
from adapters.sql_store import ServiceTypeAdapter
from adapters.sql_store import PlanAdapter
from adapters.sql_store import PlanServiceTypeAdapter
from adapters.sql_store import ManifestAdapter
from adapters.sql_store import ServiceInstanceAdapter
from adapters.sql_store import LastOperationAdapter
from adapters.sql_store import ManifestSQL


# TODO implement exception handling

from adapters.log import get_logger
import yaml

LOG = get_logger(__name__)


class Store(object):  # pragma: no cover
    def add_service(self, service: ServiceType) -> tuple:
        raise NotImplementedError

    def get_service(self, service_id: str=None) -> List[ServiceType]:
        raise NotImplementedError

    def delete_service(self, service_id: str=None) -> None:
        raise NotImplementedError

    def add_service_instance(self, service_instance: ServiceInstance) -> tuple:
        raise NotImplementedError

    def get_service_instance(self, instance_id: str=None) -> List[ServiceInstance]:
        raise NotImplementedError

    def delete_service_instance(self, service_instance_id: str=None) -> None:
        raise NotImplementedError

    def add_manifest(self, manifest: Manifest) -> tuple:
        raise NotImplementedError

    def get_manifest(self, manifest_id: str=None, plan_id: str=None) -> List[Manifest]:
        raise NotImplementedError

    def delete_manifest(self, manifest_id: str=None) -> None:
        raise NotImplementedError

    def add_last_operation(self, instance_id: str, last_operation: LastOperation) -> tuple:
        raise NotImplementedError

    def delete_last_operation(self, instance_id: str=None) -> None:
        raise NotImplementedError

    def get_last_operation(self, instance_id: str=None) -> List[LastOperation]:
        raise NotImplementedError

    def is_ok(self) -> bool:
        raise NotImplementedError


# TODO align method signatures
class SQLStore(Store):  # pragma: no cover

    def __init__(self) -> None:
        LOG.info('Using the SQLStore.')
        LOG.info('SQLStore is persistent.')

    @staticmethod
    def get_connection():
        try:
            db_helper = Helper()
            connection = pymysql.connect(
                host=db_helper.host,
                port=db_helper.port,
                user=db_helper.user,
                password=db_helper.password,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        # except BaseException as e:
        #     if "Unknown database" in str(e):
        #         conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='')
        #         return None
        except pymysql.err.OperationalError as e:
            # else:
                print('* Error connecting to DB: ', e)
                return None

    @staticmethod
    def set_up(wait_time=10):
        connection = SQLStore.get_connection()
        count = 3
        while not connection and count:
            LOG.debug('Retrying to connect to Database \'{}\'...'.format(Helper.database))
            count = count - 1
            time.sleep(wait_time)
            connection = SQLStore.get_connection()

        if connection:
            # Create DB
            connection.cursor().execute('CREATE DATABASE IF NOT EXISTS {}'.format(Helper.database))
            LOG.debug('Successfully connected to Database \'{}\'...'.format(Helper.database))
            # Create tables
            PlanAdapter.create_table()
            ServiceTypeAdapter.create_table()
            PlanServiceTypeAdapter.create_table()
            ManifestAdapter.create_table()
            ServiceInstanceAdapter.create_table()
            LastOperationAdapter.create_table()
            connection.close()
        else:
            raise Exception('Could not connect to the DB')

    @staticmethod
    def get_service(service_id: str=None) -> List[ServiceType]:
        if service_id:
            if ServiceTypeAdapter.exists_in_db(service_id):
                model_sql = ServiceTypeAdapter.find_by_id_name(service_id)
                model = ServiceTypeAdapter.model_sql_to_model(model_sql)
                return [model]
            else:
                return []
        else:
            return ServiceTypeAdapter.get_all()

    @staticmethod
    def add_service(service: ServiceType) -> tuple:
        if ServiceTypeAdapter.exists_in_db(service.id):
            return 'The service already exists in the catalog.', 409

        PlanAdapter.create_table()
        PlanServiceTypeAdapter.create_table()

        ServiceTypeAdapter.save(service)
        if ServiceTypeAdapter.exists_in_db(service.id):
            return 'Service added successfully', 200
        else:
            return 'Could not save the Service in the DB', 500

    @staticmethod
    def delete_service(service_id: str = None) -> tuple:
        if service_id:
            if ServiceTypeAdapter.exists_in_db(service_id):
                ServiceTypeAdapter.delete(service_id)
                return 'Service Deleted', 200
            else:
                return 'Service ID not found', 500
        else:
            PlanServiceTypeAdapter.delete_all()
            LastOperationAdapter.delete_all()

            ServiceInstanceAdapter.delete_all()
            ManifestAdapter.delete_all()
            ServiceTypeAdapter.delete_all()
            PlanAdapter.delete_all()
            return 'Deleted all Services', 200

    @staticmethod
    def get_manifest(manifest_id: str = None, plan_id: str = None) -> List[Manifest]:
        if manifest_id and plan_id:
            raise Exception('Query Manifests only by manifest_id OR plan_id')

        if plan_id:
            manifests = ManifestSQL.where('plan_id_name', '=', '{}'.format(plan_id)).get().serialize()
            if len(manifests) > 1:
                raise Exception('Too many manifests {mani_len} returned for the Plan: {plan_id}'.format(
                    mani_len=len(manifests), plan_id=plan_id))
            return [Manifest.from_dict(manifests[0])]

        if manifest_id:
            if ManifestAdapter.exists_in_db(manifest_id):
                model_sql = ManifestAdapter.find_by_id_name(manifest_id)
                model = ManifestAdapter.model_sql_to_model(model_sql)
                model.manifest_content = model.manifest_content.replace('</br>', '\n')
                return [model]
            else:
                return []
        else:
            manifests = ManifestAdapter.get_all()
            for manifest in manifests:
                manifest.manifest_content = manifest.manifest_content.replace('</br>', '\n')
            return manifests

    @staticmethod
    def add_manifest(manifest) -> tuple:
        if ManifestAdapter.exists_in_db(manifest.id):
            return 'The Manifest already exists in the catalog.', 409

        ''' Attempt to Create Table '''
        PlanAdapter.create_table()
        ServiceTypeAdapter.create_table()
        if ServiceTypeAdapter.exists_in_db(manifest.service_id) and PlanAdapter.exists_in_db(manifest.plan_id):
            ManifestAdapter.save(manifest)
        else:
            return 'Could not save the Manifest in the DB, Plan and Service don\'t exist', 500
        if ManifestAdapter.exists_in_db(manifest.id):
            return 'Manifest added successfully', 200
        else:
            return 'Could not save the Manifest in the DB', 500

    @staticmethod
    def delete_manifest(manifest_id: str = None):  # -> None:
        if manifest_id:
            if ManifestAdapter.exists_in_db(manifest_id):
                ManifestAdapter.delete(manifest_id)
                return 'Manifest Deleted', 200
            else:
                return 'Manifest ID not found', 500
        else:
            ManifestAdapter.delete_all()
            return 'Deleted all Manifests', 200

    @staticmethod
    def get_service_instance(instance_id: str = None) -> List[ServiceInstance]:
        if instance_id:
            if ServiceInstanceAdapter.exists_in_db(instance_id):
                model_sql = ServiceInstanceAdapter.find_by_id_name(instance_id)
                model = ServiceInstanceAdapter.model_sql_to_model(model_sql)
                return [model]
            else:
                return []
        else:
            models = ServiceInstanceAdapter.get_all()
            return models

    @staticmethod
    def add_service_instance(instance: ServiceInstance) -> tuple:
        id_name = ServiceInstanceAdapter.get_id(instance)
        if ServiceInstanceAdapter.exists_in_db(id_name):
            LOG.warning('An existing instance was attempted to be saved. Updating it...')
            SQLStore.delete_service_instance(id_name)
            # return 'The Instance already exists in the catalog.', 409

        ''' Attempt to Create Table '''
        PlanAdapter.create_table()
        ServiceTypeAdapter.create_table()
        ManifestAdapter.create_table()
        ServiceInstanceAdapter.create_table()
        LastOperationAdapter.create_table()
        ServiceInstanceAdapter.save(instance)

        id_name = ServiceInstanceAdapter.get_id(instance)
        if ServiceInstanceAdapter.exists_in_db(id_name):
            LOG.warning('Instance added successfully...')
            return 'Instance added successfully', 200
        else:
            LOG.warning('Could not save the Instance in the DB...')
            return 'Could not save the Instance in the DB', 500

    @staticmethod
    def delete_service_instance(instance_id: str = None):  # -> None:
        if instance_id:
            if ServiceInstanceAdapter.exists_in_db(instance_id):
                ServiceInstanceAdapter.delete(instance_id)
                return 'Instance Deleted', 200
            else:
                return 'Instance ID not found', 500
        else:
            LastOperationAdapter.delete_all()
            ServiceInstanceAdapter.delete_all()
            return 'Deleted all Instances', 200

    @staticmethod
    def delete_last_operation(self, instance_id: str = None) -> None:
        if instance_id:
            self.ESM_DB.last_operations.delete_one({'id': instance_id})
        else:
            self.ESM_DB.last_operations.delete_many({})

    @staticmethod
    def get_last_operation(instance_id: str = None) -> List[ServiceInstance]:
        if instance_id:
            if ServiceInstanceAdapter.exists_in_db(instance_id):
                model_sql = ServiceInstanceAdapter.find_by_id_name(instance_id)
                model = ServiceInstanceAdapter.model_sql_to_model(model_sql)
                return [model.state]
            else:
                return []
        else:
            LOG.warning('No instance ID was provided')
            return []

    @staticmethod
    def add_last_operation(instance_id: str, last_operation: LastOperation) -> tuple:
        if ServiceInstanceAdapter.exists_in_db(instance_id):
            instance = ServiceInstanceAdapter.find_by_id_name(instance_id)
            ''' Attempt to Create Table '''
            PlanAdapter.create_table()
            ServiceTypeAdapter.create_table()
            ServiceTypeAdapter.create_table()
            ServiceInstanceAdapter.create_table()
            LastOperationAdapter.create_table()
            instance.state = last_operation
            ServiceInstanceAdapter.save(instance)

            id_name = ServiceInstanceAdapter.get_id(instance)
            if ServiceInstanceAdapter.exists_in_db(id_name):
                return 'Instance added successfully', 200
            else:
                return 'Could not save the Instance in the DB', 500
        else:
            raise Exception('Service Instance not found')

    @staticmethod
    def delete_last_operation(self, instance_id: str = None) -> tuple:
        if ServiceInstanceAdapter.exists_in_db(instance_id):
            instance = ServiceInstanceAdapter.find_by_id_name(instance_id)
            ''' Attempt to Create Table '''
            PlanAdapter.create_table()
            ServiceTypeAdapter.create_table()
            ServiceTypeAdapter.create_table()
            ServiceInstanceAdapter.create_table()
            LastOperationAdapter.create_table()
            instance.state = None
            ServiceInstanceAdapter.save(instance)

            id_name = ServiceInstanceAdapter.get_id(instance)
            if ServiceInstanceAdapter.exists_in_db(id_name):
                return 'Instance added successfully', 200
            else:
                return 'Could not save the Instance in the DB', 500
        else:
            raise Exception('Service Instance not found')

    def is_ok(self):
        try:
            self.get_connection().ping()
        except:
            return False
        return True


class MongoDBStore(Store):  # pragma: no cover

    def __init__(self, host: str, port=27017) -> None:
        self.client = MongoClient(host, port)
        self.ESM_DB = self.client.esm
        LOG.info('Using the MongoDBStore.')
        LOG.info('MongoDBStore is persistent.')

    def get_service(self, service_id: str=None) -> List[ServiceType]:
        if service_id:
            if self.ESM_DB.services.count({'id': service_id}) == 1:
                return [
                    ServiceType.from_dict(
                        self.ESM_DB.services.find_one({'id': service_id})
                    )
                ]
            else:
                LOG.warning('Requested service type not found: {id}'.format(id=service_id))
                return []
        else:
            services = []

            for service in self.ESM_DB.services.find():
                services.append(
                    ServiceType().from_dict(service)
                )

            return services

    def add_service(self, service: ServiceType) -> tuple:
        if self.ESM_DB.services.count({'id': service.id}) == 0:
            result = self.ESM_DB.services.insert_one(service.to_dict())
            if not result.acknowledged:
                return 'there was an issue saving the supplied service type to the DB', 500
        else:
            self.delete_service(service_id=service.id)
            self.add_service(service=service)
            return 'the service has been updated.', 200
        return tuple()

    def delete_service(self, service_id: str=None) -> None:
        if service_id:
            self.ESM_DB.services.delete_one({'id': service_id})
        else:
            self.ESM_DB.services.delete_many({})

    def add_manifest(self, manifest: Manifest) -> tuple:
        if self.ESM_DB.manifests.count({'id': manifest.id}) == 0:
            LOG.debug("replacing newlines - mongodb strips these!")
            manifest.manifest_content = manifest.manifest_content.replace('\n', '</br>')

            result = self.ESM_DB.manifests.insert_one(manifest.to_dict())
            if not result.acknowledged:
                return 'there was an issue saving the supplied manifest to the DB', 500
        else:
            print('client side error - 4XX')
            return 'the manifest already exists in the catalog', 409

        return 'ok', 200

    def get_manifest(self, manifest_id: str=None, plan_id: str=None) -> List[Manifest]:

        if manifest_id and plan_id:
            raise Exception('Query manifests only by manifest_id OR plan_id')

        if plan_id:
            if self.ESM_DB.manifests.count({'plan_id': plan_id}) == 1:
                m = self.ESM_DB.manifests.find_one({'plan_id': plan_id})
                m = Manifest.from_dict(m)
                LOG.debug("replacing <br/> with newlines")
                m.manifest_content = m.manifest_content.replace('</br>', '\n')
                return [m]
            else:
                LOG.warning('Requested manifest by plan ID not found: {id}'.format(id=plan_id))
                return []
        elif manifest_id:
            if self.ESM_DB.manifests.count({'id': manifest_id}) == 1:
                m = self.ESM_DB.manifests.find_one({'id': manifest_id})
                m = Manifest.from_dict(m)
                LOG.debug("replacing <br/> with newlines")
                m.manifest_content = m.manifest_content.replace('</br>', '\n')
                return [m]
            else:
                LOG.warning('Requested manifest not found: {id}'.format(id=manifest_id))
                return []
        else:
            manifests = []

            for manifest in self.ESM_DB.manifests.find():
                LOG.debug("replacing <br/> with newlines")
                manifest['manifest_content'] = manifest['manifest_content'].replace('</br>', '\n')
                manifests.append(
                    Manifest().from_dict(manifest)
                )

            return manifests

    def delete_manifest(self, manifest_id: str=None) -> None:
        if manifest_id:
            self.ESM_DB.manifests.delete_one({'id': manifest_id})
        else:
            self.ESM_DB.manifests.delete_many({})

    def get_service_instance(self, instance_id: str=None) -> List[ServiceInstance]:
        if instance_id:
            if self.ESM_DB.instances.count({'context.id': instance_id}) == 1:
                return [
                    ServiceInstance.from_dict(
                        self.ESM_DB.instances.find_one({'context.id': instance_id})
                    )
                ]
            else:
                LOG.warning('Requested service instance not found: {id}'.format(id=instance_id))
                return []
        else:
            instances = []

            for inst in self.ESM_DB.instances.find():
                instances.append(
                    ServiceInstance().from_dict(inst)
                )

            return instances

    def add_service_instance(self, service_instance: ServiceInstance) -> tuple:
        result = self.ESM_DB.instances.count({'context.id': service_instance.context['id']})
        if result == 1:

            LOG.info('A duplicate service instance was attempted to be stored. '
                     'Updating the existing service instance {id}.'
                     'Content supplied:\n{content}'.format(id=service_instance.context['id'],
                                                           content=service_instance.to_str()))
            # Update the service instance

            raw_svc_inst = self.ESM_DB.instances.find_one({'context.id': service_instance.context['id']})
            record_id = raw_svc_inst['_id']
            self._sanitise_attrs(service_instance)
            result = self.ESM_DB.instances.update_one({'_id': record_id}, {"$set": service_instance.to_dict()},
                                                      upsert=False)
            if not result.acknowledged:
                return 'there was an issue updating the service instance to the DB', 500
        else:
            self._sanitise_attrs(service_instance)
            result = self.ESM_DB.instances.insert_one(service_instance.to_dict())
            if not result.acknowledged:
                return 'there was an issue saving the service instance to the DB', 500
        return tuple()

    def _sanitise_attrs(self, service_instance):
        b = dict()
        for k, v in service_instance.context.items():
            if k.find('.') > -1:
                b[k.replace('.', '_')] = v
            else:
                b[k] = v
        service_instance.context = b

    def delete_service_instance(self, service_instance_id: str=None) -> None:
        if service_instance_id:
            self.ESM_DB.instances.delete_one({'context.id': service_instance_id})
        else:
            self.ESM_DB.instances.delete_many({})

    def add_last_operation(self, instance_id: str, last_operation: LastOperation) -> tuple:
        result = self.ESM_DB.last_operations.insert_one({'id': instance_id, 'last_op': last_operation.to_dict()})
        if not result.acknowledged:
            return 'there was an issue saving the service status to the DB', 500
        return 'ok', 200

    def get_last_operation(self, instance_id: str=None) -> List[LastOperation]:
        if instance_id:
            if self.ESM_DB.last_operations.count({'id': instance_id}) == 1:
                return [
                    LastOperation.from_dict(
                        self.ESM_DB.last_operations.find_one({'id': instance_id})
                    )
                ]
            else:
                LOG.warning('Requested last operation not found: {id}'.format(id=instance_id))
                return []
        else:
            last_ops = []

            for lo in self.ESM_DB.last_operations.find():
                last_ops.append(
                    LastOperation().from_dict(lo)
                )

            return last_ops

    def delete_last_operation(self, instance_id: str=None) -> None:
        if instance_id:
            self.ESM_DB.last_operations.delete_one({'id': instance_id})
        else:
            self.ESM_DB.last_operations.delete_many({})

    def is_ok(self):
        # basic but dependent (requires client) check
        return self.client.server_info()['ok'] == 1.0


class InMemoryStore(Store):  # pragma: no cover

    # inner class as it's not used anywhere outside this class
    class DotDict(dict):
        """dot.notation access to dictionary attributes"""
        __getattr__ = dict.get
        __setattr__ = dict.__setitem__
        __delattr__ = dict.__delitem__

    def __init__(self) -> None:
        LOG.info('Using the InMemoryStore.')
        LOG.warning('InMemoryStore is not persistent.')
        self.ESM_DB = dict()
        self.ESM_DB['services'] = list()
        self.ESM_DB['instances'] = list()
        self.ESM_DB['manifests'] = list()
        self.ESM_DB['last_operations'] = list()
        self.ESM_DB = self.DotDict(self.ESM_DB)

    def get_service(self, service_id: str=None) -> List[ServiceType]:
        if not service_id:
            LOG.info('Returning registered services. Count: {count}'.format(count=len(self.ESM_DB.services)))
            return self.ESM_DB.services
        else:
            return [s for s in self.ESM_DB.services if s.id == service_id]

    def add_service(self, service: ServiceType) -> None:
        srv = [s for s in self.ESM_DB.services if s.id == service.id]
        if len(srv) > 0:
            LOG.info('Service to be updated with:\n{content}'.format(content=service.to_str()))
            self.ESM_DB.services.remove(srv[0])
            self.ESM_DB.services.append(service)
        else:
            self.ESM_DB.services.append(service)
            LOG.info('Adding a new service type to the catalog. '
                     'Content supplied: {content}'.format(content=service.to_str()))

    def delete_service(self, service_id: str=None) -> None:
        if not service_id:
            LOG.warning('Deleting ALL registered service types in the catalog.')
            self.ESM_DB.services = list()
        else:
            service_to_delete = [s for s in self.ESM_DB.services if s.id == service_id]
            if len(service_to_delete) < 1:
                LOG.error('no service instance found.')
                raise Exception('no service instance found.')
            LOG.info('Deleting the service {id} from the catalog. Content:\n{content}'.format(
                id=service_id, content=service_to_delete[0].to_str()))
            self.ESM_DB.services.remove(service_to_delete[0])

    def valid_manifest_type(self, content, type):
        mani = yaml.safe_load(content)
        if type == 'docker-compose':
            return 'version' in mani
        elif type == 'kubernetes':
            return 'apiVersion' in mani
        else:
            return True # letting all other manifests pass

    def add_manifest(self, manifest: Manifest) -> tuple:

        m = [m for m in self.ESM_DB.manifests if m.id == manifest.id]

        if len(m) == 0:
            LOG.info('Manifest to be added with:\n{content}'.format(content=manifest.to_str()))

            if not self.valid_manifest_type(manifest.manifest_content, manifest.manifest_type):
                LOG.error("Incompatible manifest type and content.")
                return 'the manifest has an incompatible type {}'.format(manifest.manifest_type), 400

            # self.ESM_DB.manifests.remove(m[0])
            self.ESM_DB.manifests.append(manifest)
            return 'ok', 200
        else:
            print('client side error - 4XX')
            error_msg = "The Manifest already exists in the catalog."
            LOG.warning(error_msg)
            return error_msg, 409
            # self.ESM_DB.manifests.append(manifest)
            # LOG.info('Adding a new service type to the catalog. '
            #          'Content supplied: {content}'.format(content=manifest.to_str()))

    def get_manifest(self, manifest_id: str=None, plan_id: str=None) -> List[Manifest]:
        if manifest_id and plan_id:
            raise Exception('you can only query by manifest_id or plan_id!')

        if not plan_id and not manifest_id:
            return self.ESM_DB.manifests
        elif plan_id:
            return [m for m in self.ESM_DB.manifests if m.plan_id == plan_id]
        elif manifest_id:
            return [m for m in self.ESM_DB.manifests if m.id == manifest_id]
        return []

    def delete_manifest(self, manifest_id: str=None) -> None:
        if not manifest_id:
            LOG.warning('Deleting ALL registered manifests in the catalog.')
            self.ESM_DB.manifests = list()
        else:
            manifest_to_delete = [m for m in self.ESM_DB.manifests if m.id == manifest_id]
            if len(manifest_to_delete) < 1:
                LOG.error('no manifest found.')
                raise Exception('no manifest found.')

            LOG.info('Deleting the manifest {id} from the catalog. Content:\n{content}'.format(
                id=manifest_id, content=manifest_to_delete[0].to_str()))
            self.ESM_DB.manifests.remove(manifest_to_delete[0])

    def add_service_instance(self, service_instance: ServiceInstance) -> None:

        si = [si for si in self.ESM_DB.instances if si.context['id'] == service_instance.context['id']]

        if len(si) > 0:
            LOG.info('Service Instance to be updated with:\n{content}'.format(content=service_instance.to_str()))
            self.ESM_DB.instances.remove(si[0])
            self.ESM_DB.instances.append(service_instance)
        else:
            self.ESM_DB.instances.append(service_instance)
            LOG.info('Adding a new service instance. '
                     'Content supplied: {content}'.format(content=service_instance.to_str()))

    def get_service_instance(self, instance_id: str=None) -> List[ServiceInstance]:
        if not instance_id:
            return self.ESM_DB.instances
        else:
            return [i for i in self.ESM_DB.instances if i.context['id'] == instance_id]

    def delete_service_instance(self, service_instance_id: str=None) -> None:
        if not service_instance_id:
            LOG.warning('Deleting ALL service instances in the catalog.')
            self.ESM_DB.instances = list()
        else:
            service_instance_to_delete = [si for si in self.ESM_DB.instances if si.context['id'] ==
                                          service_instance_id][0]
            LOG.info('Deleting the service instance {id} from the catalog. Content:\n{content}'.format(
                id=service_instance_id, content=service_instance_to_delete.to_str()))
            self.ESM_DB.instances.remove(service_instance_to_delete)

    def add_last_operation(self, instance_id: str, last_operation: LastOperation) -> None:
        last_op = {'id': instance_id, 'last_op': last_operation}

        lo = [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]

        if len(lo) > 0:
            LOG.info('An existing last operation for service instance {id} is found. '
                     'Updating with {content}'.format(id=instance_id, content=last_operation.to_str()))
            lo[0]['last_op'].state = last_operation.state
            lo[0]['last_op'].description = last_operation.description
        else:
            self.ESM_DB.last_operations.append(last_op)
            LOG.info('Adding a new last operation. '
                     'Content supplied: {content}'.format(content=str(last_op)))

        # if last_op not in self.ESM_DB.last_operations:   # this check fails - need to search by instance.id
        #     self.ESM_DB.last_operations.append(last_op)
        # else:
        #     LOG.info('An existing last operation for service instance {id} is found. '
        #              'Updating with {content}'.format(id=instance_id, content=last_operation.to_str()))
        #     lo = [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]
        #     lo[0]['last_op'].state = last_operation.state
        #     lo[0]['last_op'].description = last_operation.description

    def get_last_operation(self, instance_id: str=None) -> List[LastOperation]:
        if not instance_id:
            return self.ESM_DB.last_operations
        else:
            return [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]

    def delete_last_operation(self, instance_id: str=None) -> None:
        if not instance_id:
            LOG.warning('Deleting ALL last operations in the data store.')
            self.ESM_DB.last_operations = list()
        else:
            last_op_to_delete = [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]
            if len(last_op_to_delete) < 1:
                LOG.error('no last_operation found.')
                raise Exception('no last_operation found.')
            LOG.info('Deleting the service {id} from the catalog. Content:\n{content}'.format(
                id=instance_id, content=last_op_to_delete[0]))
            self.ESM_DB.last_operations.remove(last_op_to_delete[0])

    def is_ok(self):
        # no other logic needed - this store is in-memory
        return True


mongo_host = config.esm_mongo_host
sql_host = config.esm_sql_host
in_mem = config.esm_in_mem

if len(mongo_host) and len(sql_host):  # pragma: no cover
    raise RuntimeError('Both MongoDB and SQL data store environment variables are set. Set and use only one.')

if len(mongo_host) and in_mem == 'NO':  # pragma: no cover
    STORE = MongoDBStore(mongo_host)
elif len(sql_host) and in_mem == 'NO':  # pragma: no cover
    STORE = SQLStore()
    STORE.set_up()
else:  # pragma: no cover
    STORE = InMemoryStore()
