# FAIR Evaluator
[![GitHub license](https://img.shields.io/github/license/indigo-dc/DEEPaaS.svg)](https://github.com/indigo-dc/DEEPaaS/blob/master/LICENSE)
[![GitHub release](https://img.shields.io/github/release/indigo-dc/DEEPaaS.svg)](https://github.com/indigo-dc/DEEPaaS/releases)
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

### Develop your own plugin



#### Translations

## Evaluation tests

### RDA Indicators

[Indicators](indicators.md)

### Technical implementation
[Technical implementation](technical_implementation.md)
