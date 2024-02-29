# FAIR EVA (Evaluator, Validator & Advisor)

#### Achievements
[![SQAaaS badge](https://github.com/EOSC-synergy/SQAaaS/blob/master/badges/badges_120x93/badge_software_silver.png)](https://eu.badgr.com/public/assertions/VZzcTl6WTo-6r6yCKUFGpA "SQAaaS silver badge achieved")

[![GitHub license](https://img.shields.io/github/license/indigo-dc/DEEPaaS.svg)](https://github.com/EOSC-synergy/FAIR_eva/blob/main/LICENSE)
[![GitHub release](https://img.shields.io/github/release/indigo-dc/DEEPaaS.svg)](https://github.com/EOSC-synergy/FAIR_eva/releases)
[![Python versions](https://img.shields.io/pypi/pyversions/deepaas.svg)](https://pypi.python.org/pypi/deepaas)


# Documentation

[Documentation and guidelines for this project](docs/index.md)

## Cite as
Aguilar Gómez, F., Bernal, I. FAIR EVA: Bringing institutional multidisciplinary repositories into the FAIR picture. Sci Data 10, 764 (2023). https://doi.org/10.1038/s41597-023-02652-8

## Quickstart

```
docker run --name=fair_eva -p 9090:9090 -p 5000:5000 -dit --network host ferag/fair_eva
```

## Deployment as a service

One may deploy FAIR_eva as a service using `docker compose` and provided `compose.base.yaml` and `compose.prod.yaml` files. The running service includes:
* traefik as reverse_proxy and to obtain Letsencrypt SSL certificate
* FAIR_eva

### Configuration for deployment
Customize deployment with an `.env` file from `.env-template`.

### Deploy for (local) development

```bash
docker compose -f compose.base.yaml up -d
```

### Deploy for production

```bash
docker compose -f compose.base.yml -f compose.prod.yaml up -d
```

# Acknowledgements

This software started to be developed within EOSC-synergy receives
funding from the European Union’s Horizon 2020 research and
innovation programme under grant agreement No 857647.
