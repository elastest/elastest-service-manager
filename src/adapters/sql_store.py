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
# GENERICS
import json
import os

from orator import DatabaseManager, Schema
from orator import Model
from orator.orm import belongs_to_many
from orator.orm import belongs_to
from orator.orm import has_many

# SERVICE TYPE
from esm.models.service_type import ServiceType
from esm.models.dashboard_client import DashboardClient
from esm.models.service_metadata import ServiceMetadata
# MANIFEST
from esm.models.manifest import Manifest
# LAST OPERATION
from esm.models.last_operation import LastOperation
# PLAN
from esm.models.plan import Plan
from esm.models.plan_metadata import PlanMetadata
# INSTANCE
from esm.models.service_instance import ServiceInstance




'''    
    *******************
    *******************
    **** TESTED CODE **
    *******************
    **** INSTANCE *****
    *******************
    ******** ♥ ********
    *******************
'''


class LastOperationAdapter(LastOperation):
    @staticmethod
    def sample_model(name='instance1') -> LastOperation:
        model = LastOperation()
        model.state = name
        model.description = name
        return model

    @classmethod
    def to_blob(cls, model: LastOperation) -> dict:
        my_dict = {}
        ''' STRINGS '''
        my_dict['state'] = model.state
        my_dict['description'] = model.description

        return json.dumps(my_dict)

    @classmethod
    def from_blob(cls, blob) -> LastOperation:
        return cls.from_dict(dict(json.loads(blob)))


class ServiceInstanceSQL(Model):
    __table__ = 'service_instance'

    @belongs_to
    def service(self):
        return ServiceTypeSQL

    def __init__(self):
        super(ServiceInstanceSQL, self).__init__()
        Model.set_connection_resolver(Helper.db)

    ''' 
        UPDATE WITH:
        self.swagger_types = {
                'service_type': ServiceType, (this is a service_id)
                'state': LastOperation, (this is a operation_id)
                'context': object (no idea what kind of object...)
            }

    '''

    @classmethod
    def create_table(cls):
        with Helper.schema.create(cls.__table__) as table:
            table.increments('id')
            ''' STRINGS '''
            table.string('id_name').unique()
            ''' FOREIGN KEY '''
            table.string('service_id_name')
            table.integer('service_id').unsigned()
            table.foreign('service_id').references('id').on('service_types')
            ''' OBJECTS '''
            table.string('state')
            table.string('context').nullable()
            ''' DATES '''
            table.datetime('created_at')
            table.datetime('updated_at')

    @classmethod
    def table_exists(cls):
        return Helper.schema.has_table(cls.__table__)

    @classmethod
    def delete_all(cls):
        if Helper.schema.has_table(cls.__table__):
            # Helper.db.table(cls.__table__).truncate()
            Helper.schema.drop_if_exists(cls.__table__)


class ServiceInstanceAdapter:
    @staticmethod
    def create_table():
        if not ServiceInstanceSQL.table_exists():
            ServiceInstanceSQL.create_table()

    @staticmethod
    def sample_model(name='instance1') -> ServiceInstance:
        model = ServiceInstance()
        ''' OBJECT '''
        model.service_type = ServiceTypeAdapter.sample_model(name)
        ''' OBJECT '''
        model.state = LastOperationAdapter.sample_model(name)
        ''' OBJECT '''
        model.context = {'id': 'instance1'}
        return model

    @staticmethod
    def model_to_model_sql(model: ServiceInstance):
        model_sql = ServiceInstanceSQL()
        ''' OBJECT '''
        service_sql = ServiceTypeAdapter.find_by_id_name(model.service_type.id)
        model_sql.service_id = service_sql.id
        model_sql.service_id_name = service_sql.id_name
        ''' OBJECT '''
        model_sql.state = LastOperationAdapter.to_blob(model.state)
        ''' OBJECT '''
        model_sql.context = Helper.to_blob(model.context)
        model_sql.id_name = ServiceInstanceAdapter.get_id(model)
        return model_sql

    @classmethod
    def sample_model_sql(cls) -> ServiceInstanceSQL:
        model = cls.sample_model()
        # DANGEROUS! in case it's being transformed without saving the data of Service et al.
        return cls.model_to_model_sql(model)

    @staticmethod
    def model_sql_to_model(model_sql: ServiceInstanceSQL) -> ServiceInstance:
        model = ServiceInstance()
        ''' OBJECT '''
        service_sql = ServiceTypeAdapter.find_by_id_name(model_sql.service_id_name)
        model.service_type = ServiceTypeAdapter.model_sql_to_model(service_sql)
        ''' OBJECT '''
        model.state = LastOperationAdapter.from_blob(model_sql.state)
        ''' OBJECT '''
        model.context = Helper.from_blob(model_sql.context)
        return model

    @staticmethod
    def get_id(model: ServiceInstance):
        if type(model.context) != dict:
            raise Exception('Context type \'{}\' not supported', type(model.context))

        if 'id' in model.context:
            return dict(model.context)['id']
        else:
            return None

    @staticmethod
    def save(model: ServiceInstance) -> ServiceInstanceSQL:
        id_name = ServiceInstanceAdapter.get_id(model)
        if not id_name:
            raise Exception('ID for given instance not found!')
        model_sql = ServiceInstanceAdapter.find_by_id_name(id_name) or None
        if model_sql:
            ''' OBJECTS '''
            service_sql = ServiceTypeAdapter.find_by_id_name(model.service_type.id)
            model_sql.service_type_id = service_sql.id
            model_sql.service_type_id_name = service_sql.id_name
            ''' OBJECT '''
            model_sql.state = LastOperationAdapter.to_blob(model.state)
            ''' OBJECT '''
            model_sql.context = Helper.to_blob(model.context)
        else:
            model_sql = ServiceInstanceAdapter.model_to_model_sql(model)
            model_sql.save()
        return model_sql

    @staticmethod
    def delete_all() -> None:
        ServiceInstanceSQL.delete_all()

    @staticmethod
    def delete(id_name: str) -> None:
        model_sql = ServiceInstanceAdapter.find_by_id_name(id_name) or None
        if model_sql:
            model_sql.delete()
        else:
            raise Exception('model not found on DB to delete')

    @staticmethod
    def get_all() -> [ServiceInstance]:
        model = ServiceInstanceSQL()
        models = [] or model.all()  # .serialize()
        return [ServiceInstanceAdapter.model_sql_to_model(model) for model in models]

    @staticmethod
    def find_by_id_name(id_name: str) -> ServiceInstanceSQL or None:
        result = ServiceInstanceSQL.where('id_name', '=', '{}'.format(id_name)).get()
        if result:
            return result[0]
        else:
            return None

    @staticmethod
    def exists_in_db(id_name: str) -> bool:
        result = ServiceInstanceAdapter.find_by_id_name(id_name)
        if result:
            return True
        else:
            return False


'''
    *******************
    *******************
    **** TESTED CODE **
    *******************
    **** MANIFEST *****
    *******************
    ******** ♥ ********
    *******************
'''


class ManifestSQL(Model):
    __table__ = 'service_manifests'

    @belongs_to
    def service(self):
        return ServiceTypeSQL

    @belongs_to
    def plan(self):
        return PlanSQL

    def __init__(self):
        super(ManifestSQL, self).__init__()
        Model.set_connection_resolver(Helper.db)

    ''' 
        UPDATE WITH:
             self.swagger_types = {
                'id_name': str,
                'plan_id': str,
                'service_id': str,
                'manifest_type': str,
                'manifest_content': str,
                'endpoints': object
            }

    '''

    @classmethod
    def create_table(cls):
        with Helper.schema.create(cls.__table__) as table:
            table.increments('id')
            ''' STRINGS '''
            table.string('id_name').unique()
            table.string('manifest_type')
            table.string('manifest_content')
            ''' FOREIGN KEY '''
            table.string('service_id_name')
            table.integer('service_id').unsigned()
            table.foreign('service_id').references('id').on('service_types')
            ''' FOREIGN KEY '''
            table.string('plan_id_name')
            table.integer('plan_id').unsigned()
            table.foreign('plan_id').references('id').on('plans')
            ''' OBJECTS '''
            table.string('endpoints').nullable()
            ''' DATES '''
            table.datetime('created_at')
            table.datetime('updated_at')

    @classmethod
    def table_exists(cls):
        return Helper.schema.has_table(cls.__table__)

    @classmethod
    def delete_all(cls):
        if Helper.schema.has_table(cls.__table__):
            Helper.schema.drop_if_exists(cls.__table__)


class ManifestAdapter:
    @staticmethod
    def create_table():
        if not ManifestSQL.table_exists():
            ManifestSQL.create_table()

    @staticmethod
    def sample_model(name='manifest1') -> Manifest:
        model = Manifest()
        ''' STRINGS '''
        model.id = name
        model.plan_id = name + 'plan1'
        model.service_id = name
        model.manifest_type = name + 'type'
        model.manifest_content = name + 'content'
        ''' OBJECTS '''
        model.endpoints = {'endpoint': 'endpoint'}  # using dict
        return model

    @staticmethod
    def model_to_model_sql(model: Manifest):
        model_sql = ManifestSQL()
        ''' STRINGS '''
        model_sql.id_name = model.id
        model_sql.manifest_type = model.manifest_type
        model_sql.manifest_content = model.manifest_content
        ''' FOREIGN KEY '''
        model_sql.service_id_name = model.service_id
        service = ServiceTypeAdapter.find_by_id_name(model.service_id)
        if not service:
            raise Exception('Bad Service ID provided')
        model_sql.service_id = service.id
        ''' FOREIGN KEY '''
        model_sql.plan_id_name = model.plan_id
        plan = PlanAdapter.find_by_id_name(model.plan_id)
        if not plan:
            raise Exception('Bad Plan ID provided')
        model_sql.plan_id = plan.id
        ''' OBJECTS '''
        model_sql.endpoints = Helper.to_blob(model.endpoints)
        return model_sql

    @classmethod
    def sample_model_sql(cls) -> ManifestSQL:
        model = cls.sample_model()
        return cls.model_to_model_sql(model)

    @staticmethod
    def model_sql_to_model(model_sql: ManifestSQL) -> Manifest:
        model = Manifest()
        ''' STRINGS '''
        model.id_name = model_sql.id_name
        model.manifest_type = model_sql.manifest_type
        model.manifest_content = model_sql.manifest_content
        ''' FOREIGN KEY '''
        model.service_id = model_sql.service_id_name
        ''' FOREIGN KEY '''
        model.plan_id = model_sql.plan_id_name
        ''' OBJECTS '''
        model.endpoints = model_sql.endpoints
        return model

    @staticmethod
    def save(model: Manifest) -> ManifestSQL:
        model_sql = ManifestAdapter.find_by_id_name(model.id) or None
        if model_sql:
            ''' STRINGS '''
            model_sql.id_name = model.id
            model_sql.manifest_type = model.manifest_type
            model_sql.manifest_content = model.manifest_content
            ''' FOREIGN KEY '''
            model_sql.service_id_name = model.service_id
            service = ServiceTypeAdapter.find_by_id_name(model.service_id)
            if not service:
                raise Exception('Bad Service ID provided')
            model_sql.service_id = service.id
            ''' FOREIGN KEY '''
            model_sql.plan_id_name = model.plan_id
            plan = PlanAdapter.find_by_id_name(model.plan_id)
            if not plan:
                raise Exception('Bad Plan ID provided')
            model_sql.plan_id = PlanAdapter.find_by_id_name(model.plan_id)
            ''' OBJECTS '''
            model_sql.endpoints = Helper.to_blob(model.endpoints)
        else:
            model_sql = ManifestAdapter.model_to_model_sql(model)
            model_sql.save()
        return model_sql

    @staticmethod
    def delete_all() -> None:
        ManifestSQL.delete_all()

    @staticmethod
    def delete(id_name: str) -> None:
        model_sql = ManifestAdapter.find_by_id_name(id_name) or None
        if model_sql:
            model_sql.delete()
        else:
            raise Exception('model not found on DB to delete')

    @staticmethod
    def get_all() -> [Manifest]:
        model = ManifestSQL()
        models = [] or model.all()  # .serialize()
        return [ManifestAdapter.model_sql_to_model(model) for model in models]

    @staticmethod
    def find_by_id_name(id_name: str) -> ManifestSQL or None:
        result = ManifestSQL.where('id_name', '=', '{}'.format(id_name)).get()
        if result:
            return result[0]
        else:
            return None

    @staticmethod
    def exists_in_db(id_name: str) -> bool:
        result = ManifestAdapter.find_by_id_name(id_name)
        if result:
            return True
        else:
            return False


'''
    ********************
    ********************
    **** TESTED CODE ***
    ********************
    ****** PLAN ********
    ********************
    ******** ♥ *********
    ********************
'''


class PlanSQL(Model):
    __table__ = 'plans'

    @has_many
    def manifests(self):
        return ManifestSQL

    @belongs_to_many
    def services(self):
        return ServiceTypeSQL

    def __init__(self):
        super(PlanSQL, self).__init__()
        Model.set_connection_resolver(Helper.db)

    @classmethod
    def delete_all(cls):
        if Helper.schema.has_table(cls.__table__):
            Helper.db.table(cls.__table__).truncate()

    '''
        self.swagger_types = {
            'id': str,
            'name': str,
            'description': str,

            'free': bool,
            'bindable': bool

            'metadata': PlanMetadata,
        }
    '''

    @classmethod
    def create_table(cls):
        with Helper.schema.create(cls.__table__) as table:
            table.increments('id')
            ''' STRINGS '''
            table.string('id_name').unique()
            table.string('name').unique()
            table.string('description').nullable()
            ''' BOOLEANS '''
            table.boolean('free').nullable()
            table.boolean('bindable').nullable()
            ''' OBJECTS '''
            table.string('metadata').nullable()
            ''' DATES '''
            table.datetime('created_at')
            table.datetime('updated_at')

    @classmethod
    def table_exists(cls):
        return Helper.schema.has_table(cls.__table__)


class PlanAdapter:
    @staticmethod
    def create_table():
        if not PlanSQL.table_exists():
            PlanSQL.create_table()

    @staticmethod
    def sample_model(name='plan1') -> Plan:
        model = Plan()
        ''' STRINGS '''
        model.name = name
        model.id = name
        model.description = name
        ''' BOOLEANS '''
        model.free = True
        model.bindable = False
        ''' OBJECTS '''
        model.metadata = PlanMetadata(display_name='metadata1')
        return model

    @classmethod
    def sample_model_sql(cls) -> PlanSQL:
        model = cls.sample_model()
        return cls.model_to_model_sql(model)

    @staticmethod
    def model_sql_to_model(model_sql: PlanSQL) -> Plan:
        model = Plan()
        ''' STRINGS '''
        model.name = model_sql.name
        model.id = model_sql.id_name
        model.description = model_sql.description
        ''' BOOLEANS '''
        model.bindable = model_sql.bindable
        model.free = model_sql.free
        ''' OBJECTS '''
        model.metadata = PlanMetadataAdapter.from_blob(model_sql.metadata)
        return model

    @staticmethod
    def model_to_model_sql(model: Plan):
        model_sql = PlanSQL()
        ''' STRINGS '''
        model_sql.name = model.name
        model_sql.id_name = model.id
        model_sql.description = model.description
        ''' BOOLEANS '''
        model_sql.bindable = model.bindable
        model_sql.free = model.free
        ''' OBJECTS '''
        model_sql.metadata = PlanMetadataAdapter.to_blob(model.metadata)
        return model_sql

    @staticmethod
    def save(model: Plan) -> PlanSQL:
        model_sql = PlanAdapter.find_by_id_name(model.id) or None
        if model_sql:
            ''' STRINGS '''
            model_sql.name = model.name
            model_sql.id_name = model.id
            model_sql.description = model.description
            ''' BOOLEANS '''
            model_sql.bindable = model.bindable
            model_sql.free = model.free
            ''' OBJECTS '''
            model_sql.metadata = PlanMetadataAdapter.to_blob(model.metadata)
            model_sql.update()
        else:
            model_sql = PlanAdapter.model_to_model_sql(model)
            model_sql.save()
        return model_sql

    @staticmethod
    def delete_all() -> None:
        PlanSQL.delete_all()

    @staticmethod
    def delete(id_name: str) -> None:
        model_sql = PlanAdapter.find_by_id_name(id_name) or None
        if model_sql:
            # detach
            for manifest in model_sql.manifests:
                manifest.delete()
            for service in model_sql.services:
                model_sql.services().detach(service)
            # update
            model_sql = PlanAdapter.find_by_id_name(id_name) or None
            model_sql.delete()
        else:
            raise Exception('model not found on DB to delete')

    @staticmethod
    def get_all() -> [Plan]:
        model = PlanSQL()
        models = [] or model.all()
        return [PlanAdapter.model_sql_to_model(model) for model in models]

    @staticmethod
    def find_by_id_name(id_name: str) -> PlanSQL or None:
        result = PlanSQL.where('id_name', '=', '{}'.format(id_name)).get()
        if result:
            return result[0]
        else:
            return None

    @staticmethod
    def exists_in_db(id_name: str) -> bool:
        result = PlanAdapter.find_by_id_name(id_name)
        if result:
            return True
        else:
            return False

    @staticmethod
    def plans_sql_from_service(service: ServiceType):
        return [PlanAdapter.model_to_model_sql(plan) for plan in service.plans]

    @staticmethod
    def plans_from_service_sql(service_sql):
        return [PlanAdapter.model_sql_to_model(plan_sql) for plan_sql in service_sql.plans.all()]


class PlanMetadataAdapter(PlanMetadata):
    @classmethod
    def from_blob(cls, blob) -> PlanMetadata:
        return cls.from_dict(dict(json.loads(blob)))

    '''
           self.swagger_types = {
                'bullets': str,
                'display_name': str,
                'costs': object,
                'extras': object

    '''

    @classmethod
    def to_blob(cls, model: PlanMetadata) -> dict:
        my_dict = {}
        ''' STRINGS '''
        my_dict['bullets'] = model._bullets
        my_dict['display_name'] = model._display_name
        # TODO ambiguity | content will be lost | treated as None/List
        ''' OBJECTS '''
        my_dict['costs'] = model._costs
        my_dict['extras'] = model._extras
        return json.dumps(my_dict)


'''
    *******************
    *******************
    **** TESTED CODE **
    *******************
    *** PLAN-SERVICE **
    *******************
    ******** ♥ ********
    *******************
'''


class ServiceTypeSQL(Model):
    __table__ = 'service_types'

    @has_many('service_id')   # foreign key
    def manifests(self):
        return ManifestSQL

    @has_many('service_id')   # foreign key
    def instances(self):
        return ServiceInstanceSQL

    @belongs_to_many
    def plans(self):
        return PlanSQL

    def __init__(self):
        super(ServiceTypeSQL, self).__init__()
        Model.set_connection_resolver(Helper.db)

    @classmethod
    def delete_all(cls):
        if Helper.schema.has_table(cls.__table__):
            Helper.db.table(cls.__table__).truncate()

    @classmethod
    def create_table(cls):
        with Helper.schema.create('service_types') as table:
            table.increments('id')
            ''' STRINGS '''
            table.string('id_name').unique()
            table.string('name').unique()
            table.string('short_name')
            table.string('description').nullable()
            ''' BOOLEANS '''
            table.boolean('bindable').nullable()
            table.boolean('plan_updateable').nullable()
            ''' LISTS '''
            table.string('tags').nullable()
            table.string('requires').nullable()
            ''' OBJECTS '''
            table.string('metadata').nullable()
            table.string('dashboard_client').nullable()
            ''' DATES '''
            table.datetime('created_at')
            table.datetime('updated_at')

    @classmethod
    def table_exists(cls):
        return Helper.schema.has_table(cls.__table__)


class PlanServiceTypeSQL(Model):
    __table__ = 'plans_service_types'

    @classmethod
    def create_table(cls):
        with Helper.schema.create('plans_service_types') as table:
            table.increments('id')
            ''' STRINGS '''
            table.integer('service_type_id').unsigned()
            table.foreign('service_type_id').references('id').on('service_types')
            ''' STRINGS '''
            table.integer('plan_id').unsigned()
            table.foreign('plan_id').references('id').on('plans')

    @classmethod
    def table_exists(cls):
        return Helper.schema.has_table(cls.__table__)

    @classmethod
    def delete_all(cls):
        if Helper.schema.has_table(cls.__table__):
            Helper.schema.drop_if_exists(cls.__table__)


class PlanServiceTypeAdapter:
    @staticmethod
    def create_table():
        if not PlanServiceTypeSQL.table_exists():
            PlanServiceTypeSQL.create_table()

    @classmethod
    def delete_all(cls):
        PlanServiceTypeSQL.delete_all()


'''
    *******************
    *******************
    **** TESTED CODE **
    *******************
    ***** SERVICE *****
    *******************
    ******** ♥ ********
    *******************
'''


class ServiceTypeAdapter:
    @staticmethod
    def create_table():
        if not ServiceTypeSQL.table_exists():
            ServiceTypeSQL.create_table()

    @staticmethod
    def sample_model(name='service1') -> ServiceType:
        model = ServiceType()
        ''' STRINGS '''
        model.id = name
        model.name = name
        model.short_name = name
        model.description = 'description' + name
        ''' BOOLEANS '''
        model.bindable = False
        model.plan_updateable = False
        ''' LISTS '''
        model.tags = ['description1']
        model.requires = ['requirement1']
        ''' OBJECTS '''
        model.metadata = ServiceMetadata(display_name='metadata1')
        model.dashboard_client = DashboardClient(id='client1')
        ''' PLANS '''
        model.plans = [
            PlanAdapter.sample_model(name + 'plan1'),
            PlanAdapter.sample_model(name + 'plan2')
        ]
        return model

    @classmethod
    def sample_model_sql(cls, name='service1') -> tuple:
        model = cls.sample_model(name)
        return cls.model_to_model_sql(model)

    @staticmethod
    def model_sql_to_model(model_sql: ServiceTypeSQL) -> ServiceType:
        model = ServiceType()
        ''' STRINGS '''
        model.name = model_sql.name
        model.id = model_sql.id_name
        model.short_name = model_sql.short_name
        model.description = model_sql.description
        ''' BOOLEANS '''
        model.bindable = model_sql.bindable
        model.plan_updateable = model_sql.plan_updateable
        ''' LISTS '''
        model.tags = json.loads(model_sql.tags)
        model.requires = json.loads(model_sql.requires)
        ''' OBJECTS '''
        model.metadata = ServiceMetadataAdapter.from_blob(model_sql.metadata)
        model.dashboard_client = DashboardClientAdapter.from_blob(model_sql.dashboard_client)
        model.plans = PlanAdapter.plans_from_service_sql(model_sql)
        return model

    @staticmethod
    def model_to_model_sql(model: ServiceType) -> tuple:
        model_sql = ServiceTypeSQL()
        ''' STRINGS '''
        model_sql.name = model.name
        model_sql.id_name = model.id
        model_sql.short_name = model.short_name
        model_sql.description = model.description
        ''' BOOLEANS '''
        model_sql.bindable = model.bindable
        model_sql.plan_updateable = model.plan_updateable
        ''' LISTS '''
        model_sql.tags = json.dumps(model.tags)
        model_sql.requires = json.dumps(model.requires)
        ''' OBJECTS '''
        model_sql.metadata = ServiceMetadataAdapter.to_blob(model.metadata)
        model_sql.dashboard_client = DashboardClientAdapter.to_blob(model.dashboard_client)
        ''' PLANS are lost in translation! '''
        return model_sql, PlanAdapter.plans_sql_from_service(model)

    @staticmethod
    def save(model: ServiceType) -> ServiceTypeSQL:
        model_sql = ServiceTypeAdapter.find_by_id_name(model.id) or None
        plans_sql = []
        if model_sql:
            ''' STRINGS '''
            model_sql.name = model.name
            model_sql.id_name = model.id
            model_sql.short_name = model.short_name
            model_sql.description = model.description
            ''' BOOLEANS '''
            model_sql.bindable = model.bindable
            model_sql.plan_updateable = model.plan_updateable
            ''' LISTS '''
            model_sql.tags = json.dumps(model.tags)
            model_sql.requires = json.dumps(model.requires)
            ''' OBJECTS '''
            model_sql.metadata = ServiceMetadataAdapter.to_blob(model.metadata)
            model_sql.dashboard_client = DashboardClientAdapter.to_blob(model.dashboard_client)
            # update the associated plans
            for plan_sql in model_sql.plans:
                plan = PlanAdapter.model_sql_to_model(plan_sql)
                PlanAdapter.save(plan)
            model_sql.update()
        else:
            model_sql, plans_sql = ServiceTypeAdapter.model_to_model_sql(model)
            model_sql.save()
            for plan in plans_sql:
                plan.save()
                model_sql.plans().attach(plan)
        return model_sql

    @staticmethod
    def delete_all() -> None:
        ServiceTypeSQL.delete_all()

    @staticmethod
    def delete(id_name: str) -> None:
        model_sql = ServiceTypeAdapter.find_by_id_name(id_name) or None
        if model_sql:
            for plan in model_sql.plans:
                model_sql.plans().detach(plan)
                plan.delete()
            model_sql.delete()

        else:
            raise Exception('model not found on DB to delete')

    @staticmethod
    def get_all() -> [ServiceType]:
        model = ServiceTypeSQL()
        models = [] or model.all()
        return [ServiceTypeAdapter.model_sql_to_model(model) for model in models]

    @staticmethod
    def find_by_id_name(id_name: str) -> ServiceTypeSQL or None:
        result = ServiceTypeSQL.where('id_name', '=', '{}'.format(id_name)).get()
        if result:
            return result[0]
        else:
            return None

    @staticmethod
    def exists_in_db(id_name: str) -> bool:
        result = ServiceTypeAdapter.find_by_id_name(id_name)
        if result:
            return True
        else:
            return False


class DashboardClientAdapter(DashboardClient):
    @classmethod
    def to_blob(cls, model: DashboardClient) -> dict:
        my_dict = {}
        ''' STRINGS '''
        my_dict['id'] = model._id
        my_dict['secret'] = model._secret
        my_dict['redirect_uri'] = model._redirect_uri
        return json.dumps(my_dict)

    @classmethod
    def from_blob(cls, blob) -> DashboardClient:
        return cls.from_dict(dict(json.loads(blob)))


class ServiceMetadataAdapter(ServiceMetadata):
    @classmethod
    def to_blob(cls, model: ServiceMetadata) -> dict:
        my_dict = {}
        ''' STRINGS '''
        my_dict['display_name'] = model._display_name
        my_dict['image_url'] = model._image_url
        my_dict['long_description'] = model._long_description
        my_dict['provider_display_name'] = model._provider_display_name
        my_dict['documentation_url'] = model._documentation_url
        my_dict['support_url'] = model._support_url
        my_dict['extras'] = model._extras
        return json.dumps(my_dict)

    @classmethod
    def from_blob(cls, blob) -> ServiceMetadata:
        return cls.from_dict(dict(json.loads(blob)))


'''
    *******************
    *******************
    **** TESTED CODE **
    *******************
    ***** EXTRAS ******
    *******************
    ******** ♥ ********
    *******************
'''


class Helper:
    host = os.environ.get('DATABASE_HOST', '0.0.0.0')
    user = os.environ.get('DATABASE_USER', 'root')
    password = os.environ.get('DATABASE_PASSWORD', '')
    database = os.environ.get('DATABASE_NAME', 'mysql')
    port = int(os.environ.get('MYSQL_3306_TCP', 3306))
    config = {
        'mysql': {
            'driver': 'mysql',
            'prefix': '',
            'host': host,
            'database': database,
            'user': user,
            'password': password,
            'port': port
        }
    }
    db = DatabaseManager(config)
    schema = Schema(db)

    @staticmethod
    def to_blob(model) -> str:
        return json.dumps(model)

    @staticmethod
    def from_blob(blob) -> dict:
        return dict(json.loads(blob))
