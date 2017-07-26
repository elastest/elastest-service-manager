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

from typing import List

import os
from pymongo import MongoClient

import adapters.log

from esm.models.last_operation import LastOperation
from esm.models.manifest import Manifest
from esm.models.service_instance import ServiceInstance
from esm.models.service_type import ServiceType


# TODO implement exception handling

LOG = adapters.log.get_logger(name=__name__)


class Store(object):
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


class MongoDBStore(Store):

    def __init__(self, host: str) -> None:
        _client = MongoClient(host, 27017)
        self.ESM_DB = _client.esm
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
                LOG.warn('Requested service type not found: {id}'.format(id=service_id))
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
            return 'the service already exists in the catalog. you should resubmit with a different service.', 409
        return tuple()

    def delete_service(self, service_id: str=None) -> None:
        if service_id:
            self.ESM_DB.services.delete_one({'id': service_id})
        else:
            self.ESM_DB.services.delete_many({})

    def add_manifest(self, manifest: Manifest) -> tuple:
        if self.ESM_DB.manifests.count({'id': manifest.id}) == 0:
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
                return [
                    Manifest.from_dict(
                        self.ESM_DB.manifests.find_one({'plan_id': plan_id})
                    )
                ]
            else:
                LOG.warn('Requested manifest by plan ID not found: {id}'.format(id=plan_id))
                return []
        elif manifest_id:
            if self.ESM_DB.manifests.count({'id': manifest_id}) == 1:
                return [
                    Manifest.from_dict(
                        self.ESM_DB.manifests.find_one({'id': manifest_id})
                    )
                ]
            else:
                LOG.warn('Requested manifest not found: {id}'.format(id=manifest_id))
                return []
        else:
            manifests = []

            for manifest in self.ESM_DB.manifests.find():
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
                LOG.warn('Requested service instance not found: {id}'.format(id=instance_id))
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
            result = self.ESM_DB.instances.update_one({'_id': record_id}, {"$set": service_instance.to_dict()},
                                                      upsert=False)
            if not result.acknowledged:
                return 'there was an issue updating the service instance to the DB', 500
        else:
            result = self.ESM_DB.instances.insert_one(service_instance.to_dict())
            if not result.acknowledged:
                return 'there was an issue saving the service instance to the DB', 500
        return tuple()

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
                LOG.warn('Requested last operation not found: {id}'.format(id=instance_id))
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


class DotDict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class InMemoryStore(Store):

    def __init__(self) -> None:
        LOG.info('Using the InMemoryStore.')
        LOG.warn('InMemoryStore is not persistent.')
        self.ESM_DB = dict()
        self.ESM_DB['services'] = list()
        self.ESM_DB['instances'] = list()
        self.ESM_DB['manifests'] = list()
        self.ESM_DB['last_operations'] = list()
        self.ESM_DB = DotDict(self.ESM_DB)

    def get_service(self, service_id: str=None) -> List[ServiceType]:
        if not service_id:
            LOG.info('Returning registered services. Count: {count}'.format(count=len(self.ESM_DB.services)))
            return self.ESM_DB.services
        else:
            return [s for s in self.ESM_DB.services if s.id == service_id]

    def add_service(self, service: ServiceType) -> None:
        if service not in self.ESM_DB.services:
            self.ESM_DB.services.append(service)
            LOG.info('Adding a new service type to the catalog. '
                     'Content supplied: {content}'.format(content=service.to_str()))
        else:
            LOG.warn('A duplicate service type was attempted to be registered. '
                     'Ignoring the request. '
                     'Content supplied:\n{content}'.format(content=service.to_str()))

    def delete_service(self, service_id: str=None) -> None:
        if not service_id:
            LOG.warn('Deleting ALL registered service types in the catalog.')
            self.ESM_DB.services = list()
        else:
            service_to_delete = [s for s in self.ESM_DB.services if s.id == service_id]
            if len(service_to_delete) < 1:
                LOG.error('no service instance found.')
                raise Exception('no service instance found.')
            LOG.info('Deleting the service {id} from the catalog. Content:\n{content}'.format(
                id=service_id, content=service_to_delete[0].to_str()))
            self.ESM_DB.services.remove(service_to_delete[0])

    def add_manifest(self, manifest: Manifest) -> tuple:
        if manifest not in self.ESM_DB.manifests:
            self.ESM_DB.manifests.append(manifest)
            return 'ok', 200
        else:
            LOG.warn('A duplicate manifest was attempted to be registered. '
                     'Ignoring the request. '
                     'Content supplied:\n{content}'.format(content=manifest.to_str()))
            return 'duplicate', 400

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
            LOG.warn('Deleting ALL registered manifests in the catalog.')
            self.ESM_DB.manifests = list()
        else:
            manifest_to_delete = [m for m in self.ESM_DB.manifests if m.id == manifest_id][0]
            LOG.info('Deleting the manifest {id} from the catalog. Content:\n{content}'.format(
                id=manifest_id, content=manifest_to_delete.to_str()))
            self.ESM_DB.manifests.remove(manifest_to_delete)

    def add_service_instance(self, service_instance: ServiceInstance) -> None:
        if service_instance not in self.ESM_DB.instances:
            self.ESM_DB.instances.append(service_instance)
        else:
            LOG.info('A duplicate service instance was attempted to be stored. '
                     'Updating the existing service instance {id}.'
                     'Content supplied:\n{content}'.format(id=service_instance.context['id'],
                                                           content=service_instance.to_str()))
            instance = [i for i in self.ESM_DB.instances if i.context['id'] == service_instance.context['id']]
            self.ESM_DB.instances.remove(instance[0])
            self.ESM_DB.instances.append(service_instance)

    def get_service_instance(self, instance_id: str=None) -> List[ServiceInstance]:
        if not instance_id:
            return self.ESM_DB.instances
        else:
            return [i for i in self.ESM_DB.instances if i.context['id'] == instance_id]

    def delete_service_instance(self, service_instance_id: str=None) -> None:
        if not service_instance_id:
            LOG.warn('Deleting ALL service instances in the catalog.')
            self.ESM_DB.instances = list()
        else:
            service_instance_to_delete = [si for si in self.ESM_DB.instances if si.context['id'] ==
                                          service_instance_id][0]
            LOG.info('Deleting the service instance {id} from the catalog. Content:\n{content}'.format(
                id=service_instance_id, content=service_instance_to_delete.to_str()))
            self.ESM_DB.instances.remove(service_instance_to_delete)

    def add_last_operation(self, instance_id: str, last_operation: LastOperation) -> None:
        last_op = {'id': instance_id, 'last_op': last_operation}
        if last_op not in self.ESM_DB.last_operations:
            self.ESM_DB.last_operations.append(last_op)
        else:
            LOG.info('An existing last operation for service instance {id} is found. '
                     'Updating with {content}'.format(id=instance_id, content=last_operation.to_str()))
            lo = [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]
            lo[0]['last_op'].state = last_operation.state
            lo[0]['last_op'].description = last_operation.description

    def get_last_operation(self, instance_id: str=None) -> List[LastOperation]:
        if not instance_id:
            return self.ESM_DB.last_operations
        else:
            return [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]

    def delete_last_operation(self, instance_id: str=None) -> None:
        if not instance_id:
            LOG.warn('Deleting ALL last operations in the data store.')
            self.ESM_DB.last_operations = list()
        else:
            last_op_to_delete = [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]
            if len(last_op_to_delete) < 1:
                LOG.error('no last_operation found.')
                raise Exception('no last_operation found.')
            LOG.info('Deleting the service {id} from the catalog. Content:\n{content}'.format(
                id=instance_id, content=last_op_to_delete[0]))
            self.ESM_DB.last_operations.remove(last_op_to_delete[0])

# TODO reevaluate this!
mongo_host = os.getenv('ESM_MONGO_HOST', '')
if len(mongo_host):
    STORE = MongoDBStore(mongo_host)
else:
    STORE = InMemoryStore()
