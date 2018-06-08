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

from adapters.generic import Task
from adapters.measurer import Measurer, MeasurerFactory
from esm.models import LastOperation, ServiceInstance, Empty, BindingResponse

# TODO remove duplication in constructors


class CreateInstance(Task):

    def __init__(self, entity, context):
        super().__init__(entity, context, state='create')
        self.store = self.context['STORE']
        self.rm = self.context['RM']
        self.instance_id = self.entity.get('entity_id')
        self.entity_req = self.entity.get('entity_req')

    def run(self):

        if len(self.store.get_service_instance(instance_id=self.instance_id)) == 1:
            self.context['status'] = ('Service instance with id {id} already exists'.format(id=self.instance_id), 409)
            return self.entity, self.context

        # get the manifest for the service/plan
        svc_type = self.store.get_service(self.entity_req.service_id)[0]
        if svc_type is None:
            self.context['status'] = ('Unrecognised service requested to be instantiated', 404)
            return self.entity, self.context

        plans = svc_type.plans
        plan = [p for p in plans if p.id == self.entity_req.plan_id]
        if len(plan) <= 0:
            self.context['status'] = ('Plan {p_id} found.'.format(p_id=self.entity_req.plan_id), 404)
            return self.entity, self.context

        mani = self.store.get_manifest(plan_id=plan[0].id)
        if len(mani) <= 0:
            self.context['status'] = ('no manifest for service {plan} found.'.format(plan=self.entity_req.plan_id), 404)
            return self.entity, self.context

        mani = mani[0]

        # stored within the service instance doc
        last_op = LastOperation(state='in progress', description='service instance is being created')

        # store the instance Id with manifest id
        srv_inst = ServiceInstance(service_type=svc_type, state=last_op,
                                   context={ 'id': self.instance_id, 'manifest_id': mani.id,})

        self.store.add_service_instance(srv_inst)

        self.rm.create(instance_id=self.instance_id, content=mani.manifest_content,
                       c_type=mani.manifest_type, parameters=self.entity_req.parameters)

        # instance_id = srv_inst.context['id']

        last_op = LastOperation(state='succeeded', description='service instance is created')
        self.store.add_last_operation(instance_id=self.instance_id, last_operation=last_op)

        self.entity['entity_res'] = srv_inst
        self.context['status'] = ('created', 200)
        return self.entity, self.context


class DeleteInstance(Task):

    def __init__(self, entity, context):
        super().__init__(entity, context, state='delete')
        self.store = self.context['STORE']
        self.rm = self.context['RM']
        self.instance_id = self.entity.get('entity_id')
        self.entity_req = self.entity.get('entity_req')

    def run(self):
        instance = self.store.get_service_instance(instance_id=self.instance_id)

        if len(instance) == 1:  # XXX if greater than 1?
            mani_id = instance[0].context['manifest_id']
            mani = self.store.get_manifest(manifest_id=mani_id)
            if len(mani) < 1:
                self.entity['entity_res'] = Empty()
                self.context['status'] = ('no service manifest found.', 404)
                return self.entity, self.context

            self.rm.delete(instance_id=self.instance_id, manifest_type=mani[0].manifest_type)
            self.store.delete_service_instance(self.instance_id)

            self.entity['entity_res'] = Empty()
            self.context['status'] = ('deleted', 200)
            return self.entity, self.context
        else:
            self.entity['entity_res'] = Empty()
            self.context['status'] = ('not found', 404)
            return self.entity, self.context


class RetrieveInstance(Task):
    def __init__(self, entity, context, state='retrieve'):
        super().__init__(entity, context, state=state)
        self.store = self.context['STORE']
        self.rm = self.context['RM']
        self.instance_id = entity.get('entity_id')
        self.entity_req = entity.get('entity_req')

    def run(self):
        # service instance should already be recorded
        srv_inst = self.store.get_service_instance(self.instance_id)
        if len(srv_inst) < 1:  # if greater than 1?
            self.entity['entity_res'] = Empty()
            self.context['status'] = ('no service instance found.', 404)
            return self.entity, self.context

        srv_inst = self._get_instance(srv_inst[0])

        self.entity['entity_res'] = srv_inst
        self.context['status'] = ('service instance found.', 200)
        return self.entity, self.context

    def _get_instance(self, srv_inst):
        # get the latest info
        mani_id = srv_inst.context['manifest_id']
        mani = self.store.get_manifest(manifest_id=mani_id)
        if len(mani) < 1:
            return 'no manifest found.', 404
        # Get the latest info of the instance
        # could also use STORE.get_service_instance(srv_inst) but will not have all details
        inst_info = self.rm.info(instance_id=srv_inst.context['id'], manifest_type=mani[0].manifest_type)

        if inst_info['srv_inst.state.state'] == 'failed':
            # try epm.delete(instance_id=instance_id)?
            return 'There has been a failure in creating the service instance.', 500

        srv_inst.state.state = inst_info['srv_inst.state.state']
        srv_inst.state.description = inst_info['srv_inst.state.description']

        # don't need you any more, buh-bye!
        del inst_info['srv_inst.state.state']
        del inst_info['srv_inst.state.description']

        # merge the two context dicts
        srv_inst.context = {**srv_inst.context, **inst_info}

        # update the service instance record - there should be an asynch method doing the update - event based
        self.store.add_service_instance(srv_inst)

        return srv_inst


class RetrieveAllInstances(RetrieveInstance):
    def __init__(self, entity, context):
        super().__init__(entity, context, state='retrieve-all')

    def run(self):
        instances = self.store.get_service_instance()
        insts = list()
        for inst in instances:
            insts.append(self._get_instance(inst))

        self.entity['entity_res'] = insts
        self.context['status'] = ('service instances found.', 200)
        return self.entity, self.context


class RetrieveInstanceLastOp(RetrieveInstance):
    def __init__(self, entity, context):
        super().__init__(entity, context, state='retrieve-lastop')

    def run(self):
        entity, context = RetrieveInstance(self.entity, self.context).run()
        entity['entity_res'] = entity['entity_res'].state

        return entity, context


class BindInstance(Task):
    def __init__(self, entity, context):
        super().__init__(entity, context, state='bind')
        self.store = self.context['STORE']
        self.rm = self.context['RM']
        self.auth = self.context['AUTH']
        self.instance_id = entity.get('entity_id')
        self.entity_req = entity.get('entity_req')

    def run(self):
        svc_inst = self.store.get_service_instance(self.instance_id)[0]

        if not svc_inst.service_type.bindable:
            self.entity['entity_res'] = svc_inst
            self.context['status'] = ('The service instance does not support (un)service binding', 400)
            return self.entity, self.context

        creds = self.auth.create_credentials(self.entity_req['binding_id'], self.instance_id)
        binding = BindingResponse(credentials=creds)
        svc_inst.context['binding'] = binding.to_dict()

        # update instance with binding info
        # LOG.info('Updating the service instance info with binding details:\n' + svc_inst.to_str())
        self.store.add_service_instance(svc_inst)

        self.entity['entity_res'] = svc_inst
        self.context['status'] = ('bound.', 200)
        return self.entity, self.context


class UnbindInstance(Task):
    def __init__(self, entity, context):
        super().__init__(entity, context, state='unbind')
        self.store = self.context['STORE']
        self.rm = self.context['RM']
        self.auth = self.context['AUTH']
        self.instance_id = entity.get('entity_id')
        self.entity_req = entity.get('entity_req')

    def run(self):
        svc_inst = self.store.get_service_instance(self.instance_id)[0]
        if not svc_inst.service_type.bindable:
            self.entity['entity_res'] = svc_inst
            self.context['status'] = ('The service instance does not support (un)service binding', 400)
            return self.entity, self.context

        self.auth.delete_credentials(svc_inst.context['binding']['credentials'])

        # remove binding info
        del svc_inst.context['binding']

        # update instance with binding info
        self.store.add_service_instance(svc_inst)

        self.entity['entity_res'] = Empty()
        self.context['status'] = ('unbound.', 200)
        return self.entity, self.context


class UpdateInstance(Task):
    def __init__(self, entity, context):
        super().__init__(entity, context, state='update')
        self.store = self.context['STORE']
        self.rm = self.context['RM']
        self.instance_id = entity.get('entity_id')
        self.entity_req = entity.get('entity_req')

    def run(self):
        self.entity['entity_res'] = Empty()
        self.context['status'] = ('Not implemented', 501)

        return self.entity, self.context


class MeasureInstance(Task):
    def __init__(self, entity, context, state=''):
        super().__init__(entity, context, state)
        self.store = self.context['STORE']
        self.rm = self.context['RM']
        self.instance_id = entity.get('entity_id')
        self.entity_req = entity.get('entity_req')

    def run(self):
        pass
        # if os.environ.get('ESM_MEASURE_INSTANCES', 'NO') == 'YES':
        factory = MeasurerFactory.instance()
        factory.start_heartbeat_measurer({'instance_id': self.instance_id, 'RM': self.rm, 'mani': mani})
        # m = Measurer(cache=None)
        # factory = MeasurerFactory.instance()
        # factory.stop_heartbeat_measurer(self.instance_id)