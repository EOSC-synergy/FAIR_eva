# FAIR Evaluator
[![GitHub license](https://img.shields.io/github/license/indigo-dc/DEEPaaS.svg)](https://github.com/indigo-dc/DEEPaaS/blob/master/LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/deepaas.svg)](https://pypi.python.org/pypi/deepaas)

FAIR evaluator has been developed to check the FAIRness level of digital objects from different repositories or data portals. It requires the object identifier (preferably persistent and unique identifier) and the repository to check. It also provides a generic and agnostic way to check digital objects.

## Description
FAIR evaluator is a service that runs over the web. IT can be deployed as a stand-alone application or in a docker container. It implements different web services: the API that manages the evaluation and the web interface to facilitate accessing and user-friendliness.

## Goals
The goals of this service are:
- Checks data and metadata from a digital object
- Based on some indicators, evaluates the FAIRness of the resource.
- Provides feedback to the users to improve

## Getting started
To launch the application in an stand-alone mode, the steps are the following:
```
git clone https://github.com/EOSC-synergy/FAIR_eva.git
cd ./FAIR_eva
pip3 install -r requirements.txt
cp config.ini.template config.ini
/FAIR_eva/fair.py &
/FAIR_eva/web.py &
```
The last step, running web.py is optional if you don not want to deploy the web visual interface. The ports to run the app are 90100 for the API and 5000 for the web interface. They can be configured if needed.

### Docker version deployment
To deploy a docker container, just run the latest image:
```
docker run --name=fair_eva -p 9090:9090 -p 5000:5000 -dit --network host
```

## Architecture
FAIR evaluator implements a modular architecture to allow data services and repositories to develop new plugins to access its services. Also, some parameters can be configured like the metadata terms to check, controlled vocabularies, etc.

### Configuration
The config.ini file contains all the configuration parameters. They are distributed in different sections. To customize your FAIR evaluator deployment. It will work by default, but this is what you can edit:
```
[local]
# Defines if your service is deployed close to the data service and if it is only configured to work with that service
# only_local = true if it will run only for your service
only_local = false
repo = oai-pmh
```
The repositories or data portals that implements a plugin can be listed in the service. Ypu can configure those that you wants to appear in the list. Every repository should be shwon with the display name equal python Class name. The Generic class is "Evaluator"
```
[Repositories]
oai-pmh = 'Evaluator'
digital_csic = 'Digital.CSIC'
example_plugin = Example_Plugin
````

### Develop your own plugin



#### Translations

## Evaluation tests

### RDA Indicators

[Indicators](indicators.md)

### Technical implementation
[Technical implementation](technical_implementation.md)
