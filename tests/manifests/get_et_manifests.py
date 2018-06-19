import json
import requests
import yaml

services = [
    'elastest-user-emulator-service',
    'elastest-device-emulator-service',
    'elastest-monitoring-service',
    'elastest-bigdata-service',
    'elastest-security-service'
]

register_service = True
headers = {
            'Accept': "application/json",
            'Content-Type': "application/json",
            'X-Broker-Api-Version': "2.12",
        }

for svc in services:
    print("Getting the manifest of the {svc} service.".format(svc=svc))
    res = requests.get('https://raw.githubusercontent.com/elastest/{svc}/master/elastestservice.json'.format(svc=svc))
    content = res.json()

    if register_service:
        # register service description
        url = "http://localhost:8080/v2/et/catalog"
        payload = json.dumps(content['register'])
        response = requests.request("PUT", url, data=payload, headers=headers)

        # register manifest description
        url = "http://localhost:8080/v2/et/manifest/{id}".format(id=content['manifest']['id'])
        payload = json.dumps(content['manifest'])
        response = requests.request("PUT", url, data=payload, headers=headers)

    f = open('./elastestservice-{svc}.json'.format(svc=content['register']['short_name'].lower()), 'w')
    f.write(json.dumps(content))
    f.close()

    dc = yaml.load(content['manifest']['manifest_content'])
    f = open('./docker-compose-{svc}.yml'.format(svc=content['register']['short_name'].lower()), 'w')
    f.write(yaml.dump(dc))
    f.close()

# validate number of services registered
url = "http://localhost:8080/v2/catalog"
response = requests.request("GET", url, headers=headers)
print("Should be {expected} service registered. There are: {actual}"
      .format(expected=len(services), actual=len(response.json()['services'])))
if len(services) == len(response.json()['services']):
    print("ALL SERVICES OK!")

url = "http://localhost:8080/v2/et/manifest"
response = requests.request("GET", url, headers=headers)

print("Should be {expected} manifests registered. There are: {actual}"
      .format(expected=len(services), actual=len(response.json())))
if len(services) == len(response.json()):
    print("ALL MANIFESTS OK!")