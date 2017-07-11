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

# import pybreaker
#
#
# class LogListener(pybreaker.CircuitBreakerListener):
#     """ Listener used to log circuit breaker events. """
#
#     def __init__(self, app):
#         self.app = app
#
#     def state_change(self, cb, old_state, new_state):
#         "Called when the circuit breaker `cb` state changes."
#         self.app.logger.error('Circuit breaker state change: %r => %r', old_state.name, new_state.name)
#
#     def failure(self, cb, exc):
#         """ This callback function is called when a function called by the
#         circuit breaker `cb` fails.
#         """
#         self.app.logger.error('Circuit breaker failure: %r, count: %r', exc, cb.fail_counter)

import daiquiri

daiquiri.setup(
    # daiquiri.output.Syslog(),
    # daiquiri.output.STDERR,
    # daiquiri.output.File(directory="/var/log"),
)
LOG = daiquiri.getLogger()
