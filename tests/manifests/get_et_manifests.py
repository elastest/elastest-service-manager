import requests
import yaml

services = [
    'elastest-user-emulator-service',
    'elastest-device-emulator-service',
    'elastest-monitoring-service',
    'elastest-bigdata-service',
    'elastest-security-service'
]

for svc in services:
    print("Getting the manifest of the {svc} service.".format(svc=svc))
    res = requests.get('https://raw.githubusercontent.com/elastest/{svc}/master/elastestservice.json'.format(svc=svc))
    content = res.json()
    dc = yaml.load(content['manifest']['manifest_content'])
    f = open('./docker-compose-{svc}.yml'.format(svc=content['register']['short_name'].lower()), 'w')
    f.write(yaml.dump(dc))
    f.close()
