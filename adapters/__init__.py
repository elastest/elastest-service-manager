# Copyright 2014-2017 Zuercher Hochschule fuer Angewandte Wissenschaften
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

# import os
#
# BACKEND_IMPL = os.environ.get('SB_BACKEND', 'dummy')
# BACKEND = None
#
# if BACKEND_IMPL == 'dummy':
#     # from adapters.backend import DummyBackend
#     print(' * Using the dummy backend.')
#     # BACKEND = DummyBackend()
# elif BACKEND_IMPL == 'docker':
#     raise NotImplementedError
# elif BACKEND_IMPL == 'kubernetes':
#     raise NotImplementedError
# elif BACKEND_IMPL == 'hurtle':
#     # from adapters.backend import HurtleBackend
#     print(' * Using the hurtle backend.')
#     # BACKEND = HurtleBackend()
# else:
#     raise Exception('Unsupported backend implementation.')
