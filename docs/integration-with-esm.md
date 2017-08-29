# ESM Technical Expectations from Service Owners

The [ElasTest Service Manager (ESM)](https://github.com/elastest/elastest-service-manager) is the component that will deliver instances of the following services:

* **EUS**: [elastest-user-emulator-service](https://github.com/elastest/elastest-user-emulator-service )
* **EDS**: [elastest-device-emulator-service](https://github.com/elastest/elastest-device-emulator-service )
* **EMS**: [elastest-monitoring-service](https://github.com/elastest/elastest-monitoring-service)
* **EBS**: [elastest-bigdata-service](https://github.com/elastest/elastest-bigdata-service )
* **EDM**: [elastest-data-manager](https://github.com/elastest/elastest-data-manager)
* **ESS**: [elastest-security-service](https://github.com/elastest/elastest-security-service)



To create a service instance of any type, including the ElasTest services listed above, the service provider of the particular service type needs to provide the following two items of information.

* **Service type information**: this is essentially the business information related to the service type. It uses the OSBA data model that describes services types available in the service catalog. The OSBA data model has been extended to include the ElasTest Cost Model as is defined in WP4. It contains the following [fields that must be provided are defined the OSBA specification](https://github.com/openservicebrokerapi/servicebroker/blob/v2.12/spec.md#service-objects). Ensure the following fields are provided to ensure mandatory requirements.

  * `name`
  * `id`: this is a unique identifier that the supplier selects. It can be any string so long as it is unique within the scope of the ESM instance. The ESM will check and notify (as error) should `id` be not unique. It is *recommended* that Type-4 [UUIDs](https://en.wikipedia.org/wiki/Universally_unique_identifier) are used to ensure uniquness. This is **required**.
  * `description`
  * `bindable`
  * `plans`

  The information that you must supply in the `plans` array are:

  * `id`: this is a unique identifier that the supplier selects. It can be any string so long as it is unique within the scope of the ESM instance. The ESM will check and notify (as error) should `id` be not unique. It is *recommended* that Type-4 [UUIDs](https://en.wikipedia.org/wiki/Universally_unique_identifier) are used to ensure uniquness. This is **required**.
  * `name`
  * `description`
  * `metadata`: **This is mandatory from the ElasTest perspective** as it contains required information to calculate the cost of a TJob run.

  ElasTest extends this plan model to include the cost model defined in WP4. This cost model is used by the TORM to calculate the cost of running a TJob. In order to supply the cost information, the service provider needs to supply a JSON dictionary object named `cost` inside the `metadata` object. Below is an example of this:

  ```json
  "metadata": {
      "costs": {
          "name": "On Demand 5 + Charges",
          "type": "ONDEMAND",
          "fix_cost": {
              "deployment": 5
           },
           "var_rate": {
               "disk": 1,
  	         "memory": 10,
  	         "cpus": 50
  	     },
  	     "components": {
           },
           "description": "On Demand 5 per deployment, 50 per core, 10 per GB ram and 1 per GB disk"
      }
  }
  ```

  [A complete example of this information can be viewed in this JSON document](https://github.com/elastest/elastest-service-manager/blob/master/tests/manifests/service_registration_body.json).

* **Service manifest information**: this is the technical information related to creating a service instance. The data model is an ElasTest extension to the OSBA. It contains the following fields that must be provided by each service owner.

  * `id`: this is a unique identifier that the supplier selects. It can be any string so long as it is unique within the scope of the ESM instance. The ESM will check and notify (as error) should `id` be not unique. It is *recommended* that Type-4 [UUIDs](https://en.wikipedia.org/wiki/Universally_unique_identifier) are used to ensure uniquness. This is **required**.

  * `manifest_content`: This is the content that describes how a service components are deployed. For example, if the service is delivered by docker-compose, the `manifest_content` is the `Docker-compose` file. **Currrently, only docker-compose manifests are supported**. This is **required**.

  * `manifest_type`: Currently this can take two values:

    * `dummy`: used for testing. This will not provision any resources and return test responses.
    * `docker-compose`: This will provision the required resources (images, network) as described by the `manifest_content`

    This is **required**.

  * `plan_id`: This is the `plan_id` defined in the OSBA service information model to be used when provisioning the service instance. This is **required**.

  * `service_id`: This is the `service_id` used to describe the service type  in the Service Information document. This is **required**.

  [An example of this information can be viewed in this JSON document](https://github.com/elastest/elastest-service-manager/blob/master/tests/manifests/manifest_registration_body.json).

## Readying for TORM Integration

The 2 informations described above **must** be packaged in a JSON document.

* It must be named `elastestservice.json`. 
* Must be placed and maintained in the root respective services' code repository.

Below is the basic structure of the document:

```json
{
  register: {
      // here is where the service type information document is placed
  },
  manifest: {
      // here is where the service manifest information document is placed
  }
}
```



A complete example `elastestservice.json` [document based on the ESM test example is available here](https://github.com/elastest/elastest-service-manager/blob/master/tests/manifests/elastestservice.json).

