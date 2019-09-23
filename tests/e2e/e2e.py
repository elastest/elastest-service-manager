import json
import os
import requests


# TODO convert this into an E2E test
# bring the ESM up along with basic services by:
# docker-compose -f docker/docker-compose-tester-integration-deps.yml up

services = [
    'elastest-user-emulator-service',
    'elastest-device-emulator-service',
    'elastest-monitoring-service',
    'elastest-bigdata-service',
    'elastest-security-service'
]

headers = {
    'Accept': "application/json",
    'Content-Type': "application/json",
    'X-Broker-Api-Version': "2.12",
}


host = ""


def create_svc(name, svc_id, plan_id, delete=False):
    url = host + "/v2/service_instances/{name}".format(name=name)
    querystring = {"accept_incomplete": "false"}

    payload = {
        'organization_guid': 'org',
        'plan_id': plan_id,
        'service_id': svc_id,
        'space_guid': 'space'
    }

    response = requests.request("PUT", url, data=json.dumps(payload), headers=headers, params=querystring)
    # TODO: we should continue to poll the service via GET until the status of the service is 'ready'
    
    print(response.text)

    if delete:
        url = host + "/v2/service_instances/{name}".format(name=name)
        querystring = {
            "service_id": svc_id,
            "plan_id": plan_id,
            "accept_incomplete": "false"
        }
        response = requests.request("DELETE", url, headers=headers, params=querystring)
        print(response.text)


def report_svc_instances():
    url = host + "/v2/et/service_instances"
    response = requests.request("GET", url, headers=headers)
    print(response.text)
    print("Number of instances left running: " + str(len(response.json())))


def create_svc_instances(delete):
    # TODO: this is repetitive, should merge the IDs into the services data structure
    create_svc(name="test_eus_service_instance",
               svc_id="29216b91-497c-43b7-a5c4-6613f13fa0e9",
               plan_id="b4cfc681-0e28-41f0-b88c-dde69169a256",
               delete=delete)
    create_svc(name="test_eds_service_instance",
               svc_id="fe5e0531-b470-441f-9c69-721c2b4875f2",
               plan_id="94a1a0c7-21a0-42e3-abcd-f75f337b47c5",
               delete=delete)
    create_svc(name="test_ems_service_instance",
               svc_id="bab3ae67-8c1d-46ec-a940-94183a443825",
               plan_id="9b7dd476-462f-4a56-81b0-eccee8917cf7",
               delete=delete)
    create_svc(name="test_ebs_service_instance",
               svc_id="a1920b13-7d11-4ebc-a732-f86a108ea49c",
               plan_id="f6ed4b3e-e132-47b6-af71-26dbb76e59cb",
               delete=delete)
    create_svc(name="test_ess_service_instance",
               svc_id="af7947d9-258b-4dd1-b1ca-17450db25ef7",
               plan_id="cfd3ebd1-5afa-420d-8313-43d681168cf7",
               delete=delete)


def validate_registrations():
    url = host + "/v2/catalog"
    response = requests.request("GET", url, headers=headers)
    print("Should be {expected} service registered. There are: {actual}"
          .format(expected=len(services), actual=len(response.json()['services'])))
    if len(services) == len(response.json()['services']):
        print("All services registered OK!")

    url = host + "/v2/et/manifest"
    response = requests.request("GET", url, headers=headers)

    print("Should be *at least* {expected} manifests registered. There are: {actual}"
          .format(expected=len(services), actual=len(response.json())))
    if len(services) <= len(response.json()):
        print("All manifests registered OK!")


def register_services():
    for svc in services:
        print("Getting the manifest of the {svc} service.".format(svc=svc))
        res = requests.get(
            'https://raw.githubusercontent.com/elastest/{svc}/master/elastestservice.json'.format(svc=svc))
        content = res.json()

        # register service description
        url = host + "/v2/et/catalog"
        payload = json.dumps(content['register'])
        response = requests.request("PUT", url, data=payload, headers=headers)

        # register manifests description
        for manifest in content['manifest']:

            url = host + "/v2/et/manifest/{id}".format(id=manifest['id'])
            if bool(os.environ.get('USE_EPM', 'False')):
                manifest['manifest_type'] = 'epm'
            payload = json.dumps(manifest)

            response = requests.request("PUT", url, data=payload, headers=headers)


def run_me(delete_services):
    register_services()
    validate_registrations()
    create_svc_instances(delete=delete_services)
    report_svc_instances()


if __name__ == '__main__':
    ip = os.environ.get('ESM_EP_IP', '0.0.0.0')
    port = os.environ.get('ESM_EP_PORT', '44551')
    host = "http://" + ip + ":" + port
    del_svcs = os.environ.get('ESM_E2E_DEL_SVC', True)

    run_me(delete_services=del_svcs)
