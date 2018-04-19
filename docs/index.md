
[![][ElasTest Logo]][ElasTest]

Copyright © 2017-2019 Zuercher Hochschule fuer Angewandte Wissenschaften. Licensed under [Apache 2.0 License].

# elastest-service-manager (esm)

## Features

The service manager is based around the idea of delivering service instances to end-user consumers in an efficient and easy way to present their software to the service manager.
For this, the ElasTest Service Manager supports deployment using docker-compose descriptions and will soon support kubernetes-based descriptions.

In order to use the facility of the the ElasTest Service Manager one must use its API which is based upon the 2.12 version of the Open Service Broker API, and from which there are some specific ElasTest extensions added. 

## API Features

The following features are currently supported:

 * OSBA: list the contents of the service catalog.
 * OSBA: create a service instance.
 * OSBA: delete a service instance.
 * ElasTest Extension: get details on a service instance.
 * ElasTest Extension: register a service in the service catalog.
 * ElasTest Extension: register a service manifest (docker-compose, OpenShift/K8s[planned]) associated with a service description.

### API Features to be Implemented

The following features will be supported in upcoming releases:

 * OSBA: update a service instance

## User Documentation
Please refer to the [user docs](user-doc.md).

## Development Documentation
Please refer to the [development docs](dev-doc.md).

## Service Providers Usage

If you wish to use the ESM to deliver service instances of your software you need the following:

* All software components packaged as services within docker images.
* Those images should be available in an image registry that is accessible by the ESM
* A description of how those docker images are composed. Currently only the docker-compose/docker-swarm format is supported. Kubernetes will be supported through the use of Helm templates.

Once these items are available then the service provider simply needs to:

* Register the service with the ESM's catalog
* Register the service manifest with the ESM

# Source

Source code for other ElasTest projects can be found in the [GitHub ElasTest Group].

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
<!--stackedit_data:
eyJoaXN0b3J5IjpbOTUwMzQ5Nzc5XX0=
-->
