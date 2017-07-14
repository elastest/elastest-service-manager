from typing import List

from pymongo import MongoClient

from esm.models import Manifest
from esm.models import ServiceType
from esm.models import ServiceInstance
from esm.models import LastOperation

from adapters.log import LOG

# TODO standardise on return type of None or tuple for relevant store operations


class Store(object):
    def add_service(self, service: ServiceType) -> None:
        raise NotImplementedError

    def get_service(self, service_id: str=None) -> List[ServiceType]:
        raise NotImplementedError

    def delete_service(self, service_id: str=None) -> None:
        raise NotImplementedError

    def add_service_instance(self, service_instance: ServiceInstance) -> None:
        raise NotImplementedError

    def get_service_instance(self, instance_id: str=None) -> List[ServiceInstance]:
        raise NotImplementedError

    def delete_service_instance(self, service_instance_id: str=None) -> None:
        raise NotImplementedError

    def add_manifest(self, manifest: Manifest) -> None:
        raise NotImplementedError

    def get_manifest(self, plan_id: str=None) -> List[Manifest]:
        raise NotImplementedError

    def delete_manifest(self, manifest_id: str=None) -> None:
        raise NotImplementedError

    def add_last_operation(self, instance_id: str, last_operation: LastOperation) -> None:
        raise NotImplementedError

    def delete_last_operation(self, instance_id: str=None) -> None:
        raise NotImplementedError

    def get_last_operation(self, instance_id: str=None) -> List[LastOperation]:
        raise NotImplementedError


class MongoDBStore(Store):

    def __init__(self) -> None:
        # TODO make mongo host configurable - take from env
        _client = MongoClient('localhost', 27017)
        self.ESM_DB = _client.esm
        LOG.info('Using the MongoDBStore.')
        LOG.info('MongoDBStore is persistent.')

    def get_service(self, service_id: str=None) -> List[ServiceType]:
        if service_id:
            return [
                ServiceType.from_dict(
                    self.ESM_DB.services.find_one({'id': service_id})
                )
            ]
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

    def delete_service(self, service_id: str=None) -> None:
        if service_id:
            self.ESM_DB.services.delete_one({'id': service_id})
        else:
            self.ESM_DB.services.delete_many({})

    def add_manifest(self, manifest: Manifest) -> tuple:
        # ensure the manifest-defined service and plan id exist
        if self.ESM_DB.services.count({'id': manifest.service_id}) > 0:
            # get the plans
            plans = self.ESM_DB.services.find_one({'id': manifest.service_id})['plans']
            # filter the plans to find the plan to be associated with
            plan = [p for p in plans if p['id'] == manifest.plan_id]
            if len(plan) != 1:
                return 'no plan or duplicate plan found.', 401
        else:
            return 'the service id in the supplied manifest does not exist.', 404

        # save to DB
        if self.ESM_DB.manifests.count({'id': manifest.id}) == 0:
            result = self.ESM_DB.manifests.insert_one(manifest.to_dict())
            if not result.acknowledged:
                return 'there was an issue saving the supplied manifest to the DB', 500
        else:
            # raise Exception('Client side error - manifest already exists in the catalog!')
            print('client side error - 4XX')
            return 'the manifest already exists in the catalog', 409

    def get_manifest(self, plan_id: str=None) -> List[Manifest]:
        if plan_id:
            return [
                Manifest.from_dict(
                    self.ESM_DB.manifests.find_one({'plan_id': plan_id})
                )
            ]
        else:
            manifests = []

            for manifest in self.ESM_DB.manifests.find():
                manifests.append(
                    Manifest().from_dict(manifest)
                )

            return manifests

    def delete_manifest(self, manifest_id: str=None) -> None:
        if manifest_id:
            self.ESM_DB.manifests.find_one({'id': manifest_id})
        else:
            self.ESM_DB.manifests.delete_many({})

    def get_service_instance(self, instance_id: str=None) -> List[ServiceInstance]:
        if instance_id:
            return [
                ServiceInstance.from_dict(
                    self.ESM_DB.instances.find_one({'context.id': instance_id})
                )
            ]
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
                     'Content supplied:\n{content}'.format(id=service_instance.context['id'], content=service_instance.to_str()))
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

    def delete_service_instance(self, service_instance_id: str=None) -> None:
        if service_instance_id:
            self.ESM_DB.instances.find_one({'context.id': service_instance_id})
        else:
            self.ESM_DB.instances.delete_many({})

    def add_last_operation(self, instance_id: str, last_operation: LastOperation) -> tuple:
        result = self.ESM_DB.last_operations.insert_one({'id': instance_id, 'last_op': last_operation.to_dict()})
        if not result.acknowledged:
            return 'there was an issue saving the service status to the DB', 500

    def get_last_operation(self, instance_id: str=None) -> List[LastOperation]:
        if instance_id:
            return [
                LastOperation.from_dict(
                    self.ESM_DB.last_operations.find_one({'id': instance_id})
                )
            ]
        else:
            last_ops = []

            for lo in self.ESM_DB.last_operations.find():
                last_ops.append(
                    LastOperation().from_dict(lo)
                )

            return last_ops

    def delete_last_operation(self, instance_id: str=None) -> None:
        if instance_id:
            self.ESM_DB.last_operations.find_one({'id': instance_id})
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
            LOG.info('Returning registered services. Count: '.format(count=len(self.ESM_DB.services)))
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
            service_to_delete = [s for s in self.ESM_DB.services if s.id == service_id][0]
            LOG.info('Deleting the service {id} from the catalog. Content:\n{content}'.format(
                id=service_id, content=service_to_delete.to_str()))
            # TODO this will fail if service_to_delete is None
            self.ESM_DB.services.remove(service_to_delete)

    def add_manifest(self, manifest: Manifest) -> None:
        if manifest not in self.ESM_DB.manifests:
            self.ESM_DB.manifests.append(manifest)
        else:
            LOG.warn('A duplicate manifest was attempted to be registered. '
                     'Ignoring the request. '
                     'Content supplied:\n{content}'.format(content=manifest.to_str()))

    def get_manifest(self, manifest_id: str=None, plan_id: str=None) -> List[Manifest]:
        if manifest_id and plan_id:
            raise Exception('you can only query by manifest_id or plan_id!')

        if not plan_id and not manifest_id:
            return self.ESM_DB.manifests
        elif plan_id:
            return [m for m in self.ESM_DB.manifests if m.plan_id == plan_id]
        elif manifest_id:
            return [m for m in self.ESM_DB.manifests if m.id == manifest_id]

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
                     'Content supplied:\n{content}'.format(id=service_instance.context['id'], content=service_instance.to_str()))
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
            service_instance_to_delete = [si for si in self.ESM_DB.instances if si.context['id'] == service_instance_id][0]
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
            last_op_to_delete = [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id][0]
            LOG.info('Deleting the service {id} from the catalog. Content:\n{content}'.format(
                id=instance_id, content=last_op_to_delete))
            # TODO this will fail if last_op_to_delete is None
            self.ESM_DB.last_operations.remove(last_op_to_delete)

# TODO reevaluate this!
STORE = InMemoryStore()
