# Copyright 2017-2019 Zuercher Hochschule fuer Angewandte Wissenschaften
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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


from threading import Thread


class AsychExe(Thread):
    """
    Only purpose of this thread is to execute a list of tasks sequentially
    as a background "thread".
    """
    def __init__(self, tasks, store=None):
        super(AsychExe, self).__init__()
        self.store = store
        self.tasks = tasks

    def run(self):
        super(AsychExe, self).run()
        print('Starting AsychExe thread')

        for task in self.tasks:
            entity, extras = task.run()
            if self.store:
                print('Updating entity in store')


# TODO look into asyncio and asyncio.Task
class Task:
    def __init__(self, entity=None, context=None, state=''):
        self.entity = entity
        self.context = context
        self.state = state
        self.start_time = ''

    def run(self):
        raise NotImplemented()

    def start(self):
        return self.run()


class SynchExe(Task):
    def __init__(self, entity, context):
        super().__init__(entity, context, state='exe-serial')
        self.entity = entity  # the set of tasks to run in series

    def run(self):
        print('Starting SynchExe')

        for task in self.entity:
            entity, extras = task.run()
