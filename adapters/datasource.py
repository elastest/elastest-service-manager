from typing import List

from pymongo import MongoClient

from esm.models import Manifest
from esm.models import ServiceType
from esm.models import ServiceInstance
from esm.models import LastOperation


class Store(object):
    def add_service(self, service) -> None:
        pass

    def get_service(self, service_id=None) -> List[ServiceType]:
        pass

    def delete_service(self) -> None:
        pass

    def add_service_instance(self, service_instance) -> None:
        pass

    def get_service_instance(self, instance_id=None) -> List[ServiceInstance]:
        pass

    def delete_service_instance(self, service_instance_id=None) -> None:
        pass

    def add_manifest(self, manifest) -> None:
        pass

    def get_manifest(self, plan_id=None) -> List[Manifest]:
        pass

    def delete_manifest(self, manifest_id=None) -> None:
        pass

    def add_last_operation(self, instance_id, last_operation) -> None:
        pass

    def delete_last_operation(self, instance_id=None) -> None:
        pass

    def get_last_operation(self, instance_id=None) -> List[LastOperation]:
        pass


class MongoDBStore(Store):

    def __init__(self) -> None:
        _client = MongoClient('localhost', 27017)  # take from env
        self.ESM_DB = _client.esm

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

    def add_service(self, service):
        if self.ESM_DB.services.count({'id': service.id}) == 0:
            result = self.ESM_DB.services.insert_one(service.to_dict())
            if not result.acknowledged:
                return 'there was an issue saving the supplied service type to the DB', 500
        else:
            return 'the service already exists in the catalog. you should resubmit with a different service.', 409

    def delete_service(self, service_id=None):
        if service_id:
            self.ESM_DB.services.delete_one({'id': service_id})
        else:
            self.ESM_DB.services.delete_many({})

    def add_manifest(self, manifest):
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

    def get_manifest(self, plan_id=None) -> List[Manifest]:
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

    def delete_manifest(self, manifest_id=None):
        if manifest_id:
            self.ESM_DB.manifests.find_one({'id': manifest_id})
        else:
            self.ESM_DB.manifests.delete_many({})

    def get_service_instance(self, instance_id=None) -> List[ServiceInstance]:
        if instance_id:
            return self.ESM_DB.instances.find_one({'context.id': instance_id})
        else:
            instances = []

            for inst in self.ESM_DB.instances.find():
                instances.append(
                    ServiceInstance().from_dict(inst)
                )

            return instances

    def add_service_instance(self, service_instance: ServiceInstance):
        result = self.ESM_DB.instances.count({'context.id': service_instance.context['id']})
        if result == 1:
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

    def delete_service_instance(self, service_instance_id=None):
        if service_instance_id:
            self.ESM_DB.instances.find_one({'context.id': service_instance_id})
        else:
            self.ESM_DB.instances.delete_many({})

    def add_last_operation(self, instance_id, last_operation):
        result = self.ESM_DB.last_operations.insert_one({'id': instance_id, 'last_op': last_operation.to_dict()})
        if not result.acknowledged:
            return 'there was an issue saving the service status to the DB', 500

    def get_last_operation(self, instance_id=None):
        if instance_id:
            return self.ESM_DB.last_operations.find_one({'id': instance_id})
        else:
            last_ops = []

            for lo in self.ESM_DB.last_operations.find():
                last_ops.append(
                    LastOperation().from_dict(lo)
                )

            return last_ops

    def delete_last_operation(self, instance_id=None):
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
        self.ESM_DB = dict()
        self.ESM_DB['services'] = list()
        self.ESM_DB['instances'] = list()
        self.ESM_DB['manifests'] = list()
        self.ESM_DB['last_operations'] = list()
        self.ESM_DB = DotDict(self.ESM_DB)

    def get_service(self, service_id=None) -> List[ServiceType]:
        if not service_id:
            return self.ESM_DB.services
        else:
            return [s for s in self.ESM_DB.services if s.id == service_id]

    def add_service(self, service: ServiceType):
        self.ESM_DB.services.append(service)

    def delete_service(self, service_id=None):
        if not service_id:
            self.ESM_DB.services = list()
        else:
            self.ESM_DB.services.remove([s for s in self.ESM_DB.services if s.id == service_id][0])

    def add_manifest(self, manifest: Manifest):
        self.ESM_DB.manifests.append(manifest)

    def get_manifest(self, manifest_id=None, plan_id=None) -> List[Manifest]:
        if manifest_id and plan_id:
            raise Exception('you can only query by manifest_id or plan_id!')

        if not plan_id and not manifest_id:
            return self.ESM_DB.manifests
        elif plan_id:
            return [m for m in self.ESM_DB.manifests if m.plan_id == plan_id]
        elif manifest_id:
            return [m for m in self.ESM_DB.manifests if m.id == manifest_id]

    def delete_manifest(self, manifest_id=None):
        if not manifest_id:
            self.ESM_DB.manifests = list()
        else:
            self.ESM_DB.manifests.remove([m for m in self.ESM_DB.manifests if m.id == manifest_id][0])

    def add_service_instance(self, service_instance: ServiceInstance):
        self.ESM_DB.instances.append(service_instance)

    def get_service_instance(self, instance_id=None) -> List[ServiceInstance]:
        if not instance_id:
            return self.ESM_DB.instances
        else:
            return [i for i in self.ESM_DB.instances if i.context['id'] == instance_id]

    def delete_service_instance(self, service_instance_id=None):  # state: str=None
        if not service_instance_id:
            self.ESM_DB.instances = list()
        else:
            self.ESM_DB.instances.remove(
                [si for si in self.ESM_DB.instances if si.context['id'] == service_instance_id][0]
            )

    def add_last_operation(self, instance_id, last_operation):
        self.ESM_DB.last_operations.append({'id': instance_id, 'last_op': last_operation})

    def get_last_operation(self, instance_id=None):
        if not instance_id:
            return self.ESM_DB.last_operations
        else:
            return [lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id]

    def delete_last_operation(self, instance_id=None):
        if not instance_id:
            self.ESM_DB.last_operations = list()
        else:
            self.ESM_DB.last_operations.remove([lo for lo in self.ESM_DB.last_operations if lo['id'] == instance_id][0])


STORE = InMemoryStore()
