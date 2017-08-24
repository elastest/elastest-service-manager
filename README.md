[![][ElasTest Logo]][ElasTest]

Copyright © 2017-2019 Zuercher Hochschule fuer Angewandte Wissenschaften. Licensed under [Apache 2.0 License].

# elastest-service-manager (esm)

[![License badge](https://img.shields.io/badge/license-Apache2-orange.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![Documentation badge](https://img.shields.io/badge/docs-latest-brightgreen.svg)](http://elastest.io/docs/api/esm/)
[![Build Status](https://travis-ci.org/elastest/elastest-service-manager.svg?branch=master)](https://travis-ci.org/elastest/elastest-service-manager)
[![codecov](https://codecov.io/gh/elastest/elastest-service-manager/branch/master/graph/badge.svg)](https://codecov.io/gh/elastest/elastest-service-manager)

This is the elastest service manager that is responsible for providing support service instances to test jobs. 
It's an implementation of the [Open Service Broker API](https://github.com/openservicebrokerapi/servicebroker), v2.12, 
with further extensions ([See the spec for further details](http://petstore.swagger.io/?url=https://raw.githubusercontent.com/elastest/elastest-service-manager/master/api.yaml)).

# What is ElasTest

This repository is part of [ElasTest], which is an open source elastic platform
aimed to simplify end-to-end testing. ElasTest platform is based on three
principles: i) Test orchestration: Combining intelligently testing units for
creating a more complete test suite following the “divide and conquer” principle.
ii) Instrumentation and monitoring: Customizing the SuT (Subject under Test)
infrastructure so that it reproduces real-world operational behavior and allowing
to gather relevant information during testing. iii) Test recommendation: Using machine
learning and cognitive computing for recommending testing actions and providing
testers with friendly interactive facilities for decision taking.

# Documentation

The [ElasTest] project provides detailed documentation including tutorials,
installation and development guide.

Detailed documentation on the ESM can be found under the `docs` directory.

# Source
Source code for other ElasTest projects can be found in the [GitHub ElasTest
Group].

# Support
If you need help and support with the ESM, please refer to the ElasTest [Bugtracker]. 
Here you can find the help you need.

# News
Follow us on Twitter @[ElasTest Twitter].

# Contribution Policy
You can contribute to the ElasTest community through bug-reports, bug-fixes,
new code or new documentation. For contributing to the ElasTest community,
you can use the issue support of GitHub providing full information about your
contribution and its value. In your contributions, you must comply with the
following guidelines

* You must specify the specific contents of your contribution either through a
  detailed bug description, through a pull-request or through a patch.
* You must specify the licensing restrictions of the code you contribute.
* For newly created code to be incorporated in the ElasTest code-base, you
  must accept ElasTest to own the code copyright, so that its open source
  nature is guaranteed.
* You must justify appropriately the need and value of your contribution. The
  ElasTest project has no obligations in relation to accepting contributions
  from third parties.
* The ElasTest project leaders have the right of asking for further
  explanations, tests or validations of any code contributed to the community
  before it being incorporated into the ElasTest code-base. You must be ready
  to addressing all these kind of concerns before having your code approved.

# Licensing and distribution
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


[Apache 2.0 License]: http://www.apache.org/licenses/LICENSE-2.0
[ElasTest]: http://elastest.io/
[ElasTest Logo]: http://elastest.io/images/logos_elastest/elastest-logo-gray-small.png
[ElasTest Twitter]: https://twitter.com/elastestio
[GitHub ElasTest Group]: https://github.com/elastest
[Bugtracker]: https://github.com/elastest/bugtracker
